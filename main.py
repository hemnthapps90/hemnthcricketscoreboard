import os
import sys
import json
import time
import requests
import re
import threading
import http.server
import socketserver
import webbrowser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def start_local_server(port=8000):
    """Local server ko background mein run karne ke liye function"""
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Terminal ko clean rakhne ke liye server ke logs band kar rahe hain
    class QuietHandler(Handler):
        def log_message(self, format, *args):
            pass 

    try:
        # allow_reuse_address taaki agar script restart karein to 'Address already in use' error na aaye
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", port), QuietHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        pass # Silently handle

def scrape_player_stats(profile_url):
    """Player ki profile open karke uske Batting stats scrape karne ka function with fallback domain"""
    stats = []
    if not profile_url:
        return stats
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    # Backup domain logic: Agar ek fail ho to dusra try kare
    urls_to_try = [profile_url]
    if 'crex.com' in profile_url:
        urls_to_try.append(profile_url.replace('crex.com', 'crex.live'))
    elif 'crex.live' in profile_url:
        urls_to_try.append(profile_url.replace('crex.live', 'crex.com'))

    for url in urls_to_try:
        try:
            # Fetch player profile page
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the Batting Section
                career_sections = soup.find_all('section', class_='careerSection')
                batting_section = None
                
                for sec in career_sections:
                    title = sec.find('p', class_='careerTitle')
                    if title and 'Batting' in title.text:
                        batting_section = sec
                        break
                
                # Extract Table Data
                if batting_section:
                    table = batting_section.find('table')
                    if table:
                        rows = table.find('tbody').find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 13: # Ensuring it's a data row and not a header
                                stats.append({
                                    "Format": cols[0].text.strip(),
                                    "Mat": cols[1].text.strip(),
                                    "Inn": cols[2].text.strip(),
                                    "R": cols[3].text.strip(),
                                    "100s": cols[4].text.strip(),
                                    "50s": cols[5].text.strip(),
                                    "HS": cols[6].text.strip(),
                                    "SR": cols[7].text.strip(),
                                    "Avg": cols[8].text.strip(),
                                    "Fours": cols[9].text.strip(),
                                    "Sixes": cols[10].text.strip(),
                                    "Duck": cols[11].text.strip(),
                                    "Rank": cols[12].text.strip()
                                })
                # Agar success ho gaya, to return data immediately
                return stats
            else:
                pass # Silenced

        except requests.exceptions.Timeout:
            pass # Silenced
        except Exception as e:
            pass # Silenced
            
    return stats


def extract_players_from_soup(soup):
    """Playing XI ke rows ko scrape karne ka helper function"""
    players = []
    playing_xi_rows = soup.find_all('div', class_='playingxi-card-row')
    
    for row in playing_xi_rows:
        a_tag = row.find('a')
        full_name = a_tag['title'] if a_tag and a_tag.has_attr('title') else ""
        
        # Player Profile URL nikalna
        profile_url = a_tag['href'] if a_tag and a_tag.has_attr('href') else ""
        if profile_url and profile_url.startswith('/'):
            # Default to crex.com as primary since crex.live is frequently timing out
            profile_url = f"https://crex.com{profile_url}"
            
        p_name_div = row.find('div', class_='p-name')
        short_name = p_name_div.text.strip() if p_name_div else ""
        
        name = full_name if full_name else short_name
        
        special_tag = ""
        if p_name_div:
            sibling = p_name_div.find_next_sibling('div')
            if sibling and sibling.text.strip():
                special_tag = sibling.text.strip()
                name = f"{name} {special_tag}"
        
        role_div = row.find('div', class_='bat-ball-type')
        role = role_div.text.strip() if role_div else ""
        
        imgs = row.find_all('img')
        head_img = imgs[0]['src'] if len(imgs) > 0 else ""
        jersey_img = imgs[1]['src'] if len(imgs) > 1 else ""
        
        players.append({
            "name": name.strip(),
            "role": role,
            "profile_url": profile_url,
            "head_image_url": head_img,
            "jersey_image_url": jersey_img,
            "batting_stats": [] # Ye data aage fetch hoke fill hoga
        })
    return players


def scrape_info_data(driver, live_url):
    """Ye function sirf ek baar chalega, Toss, Playing XI aur baki Match Info nikalne ke liye"""
    clean_url = live_url.rstrip('/')
    info_url = clean_url[:-4] + "info"
    
    info_data = {
        "toss": "",
        "team_form": {},
        "head_to_head": {},
        "team_comparison": [],
        "weather": {},
        "venue_stats": {},
        "playing_xi": {}
    }
    
    driver.get(info_url)
            
    try:
        # Page load hone ka wait (jab tak team buttons na aa jayein)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.playingxi-button"))
        )
        time.sleep(2) # Extra buffer time for images
        
        soup_info = BeautifulSoup(driver.page_source, 'html.parser')
        
        # --- TOSS DETAILS ---
        toss_wrap = soup_info.find('div', class_='toss-wrap')
        if toss_wrap and toss_wrap.find('p'):
            info_data["toss"] = toss_wrap.find('p').text.strip()
            
        # --- TEAM FORM (Last 5 matches & Flag URL) ---
        try:
            format_matches = soup_info.find_all('div', class_='format-match')
            for match in format_matches:
                team_name_div = match.find('div', class_='form-team-name')
                img_tag = match.find('img', class_='form-team-img')
                if team_name_div:
                    t_name = team_name_div.text.strip()
                    flag_url = img_tag['src'] if img_tag else ""
                    # win/loss match classes dhoondna (sirf W aur L)
                    wl_elements = match.find_all('div', class_=re.compile(r'(win|loss) match'))
                    form_list = [el.text.strip() for el in wl_elements if el.text.strip() in ['W', 'L']]
                    
                    info_data["team_form"][t_name] = {
                        "flag_url": flag_url,
                        "form": form_list
                    }
        except Exception as e:
            pass

        # --- HEAD TO HEAD (Team Wins) ---
        try:
            h2h_header = soup_info.find('div', class_='team-wins-card')
            if h2h_header:
                parent_card = h2h_header.find_parent('div', class_='team-header-card')
                if parent_card:
                    team1_div = parent_card.find('div', class_='team1')
                    team2_div = parent_card.find('div', class_='team2')
                    wins_div = parent_card.find('div', class_='team-wins')
                    
                    if team1_div and team2_div and wins_div:
                        t1_name = team1_div.find('div', class_='team-name').text.strip()
                        t1_img = team1_div.find('img')['src'] if team1_div.find('img') else ""
                        t1_wins = wins_div.find('div', class_='team1-wins').text.strip()
                        
                        t2_name = team2_div.find('div', class_='team-name').text.strip()
                        t2_img = team2_div.find('img')['src'] if team2_div.find('img') else ""
                        t2_wins = wins_div.find('div', class_='team2-wins').text.strip()
                        
                        info_data["head_to_head"] = {
                            "team1": {"name": t1_name, "flag_url": t1_img, "wins": t1_wins},
                            "team2": {"name": t2_name, "flag_url": t2_img, "wins": t2_wins}
                        }
        except Exception as e:
            pass

        # --- TEAM COMPARISON (Last 10 Matches Table) ---
        try:
            comp_section = soup_info.find('div', class_='team-form-comp')
            if comp_section:
                comp_parent = comp_section.find_parent('div', class_='content-wrap')
                if comp_parent:
                    table = comp_parent.find('table', class_='table')
                    if table:
                        rows = table.find('tbody').find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) == 3:
                                t1_val = cols[0].text.strip()
                                metric = cols[1].text.strip()
                                t2_val = cols[2].text.strip()
                                info_data["team_comparison"].append({
                                    "metric": metric,
                                    "team1_value": t1_val,
                                    "team2_value": t2_val
                                })
        except Exception as e:
            pass

        # --- WEATHER INFO ---
        try:
            weather_wrap = soup_info.find('div', class_='weather-wrap')
            if weather_wrap:
                place = weather_wrap.find('div', class_='weather-place-hum-text')
                if place: info_data["weather"]['location'] = place.text.strip()
                
                temp = weather_wrap.find('div', class_='weather-temp')
                if temp: info_data["weather"]['temperature'] = temp.text.strip()
                
                condition = weather_wrap.find('div', class_='weather-cloudy-text')
                if condition: info_data["weather"]['condition'] = condition.text.strip()
                
                hum_texts = weather_wrap.find_all('div', class_='weather-place-hum-text')
                for ht in hum_texts:
                    text = ht.text.strip()
                    if 'Humidity' in text:
                        info_data["weather"]['humidity'] = text.replace('(Humidity)', '').strip()
                    elif 'Chance' in text:
                        info_data["weather"]['rain_chance'] = text.strip()
        except Exception as e:
            pass

        # --- VENUE STATS (Pace vs Spin) ---
        try:
            pace_wrap = soup_info.find('div', class_='venue-pace-wrap')
            if pace_wrap:
                cols = pace_wrap.find_all('div', class_=re.compile(r'flex-coloum'))
                for col in cols:
                    label_div = col.find('div', class_='pace-text')
                    count_div = col.find('div', class_='wicket-count')
                    if label_div and count_div:
                        label = label_div.text.strip().lower()
                        info_data["venue_stats"][f"{label}_wickets"] = count_div.text.strip()
                        
                formats = pace_wrap.find_all('div', class_='s-format')
                if len(formats) >= 2:
                    info_data["venue_stats"]['pace_percentage'] = formats[0].text.strip()
                    info_data["venue_stats"]['spin_percentage'] = formats[1].text.strip()
        except Exception as e:
            pass
            
        # --- PLAYING XI ---
        team_buttons = driver.find_elements(By.CSS_SELECTOR, "button.playingxi-button")
        
        if len(team_buttons) >= 2:
            # TEAM 1 DATA
            team1_name = team_buttons[0].text.strip()
            team1_players = extract_players_from_soup(soup_info)
            
            for p in team1_players:
                p['batting_stats'] = scrape_player_stats(p['profile_url'])
                
            info_data["playing_xi"][team1_name] = team1_players
            
            # --- BUTTON CLICK FOR TEAM 2 USING XPATH ---
            xpath_team2 = "/html/body/app-root/div/app-match-details/div[3]/div/app-match-info/div/div[2]/div[2]/app-playingxi-card/div/div[1]/div/button[2]"
            try:
                team2_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_team2))
                )
                team2_name = team2_btn.text.strip()
                driver.execute_script("arguments[0].click();", team2_btn)
                time.sleep(3) # Team 2 ka data Angular render hone ka wait
                
                # TEAM 2 DATA
                soup_info_team2 = BeautifulSoup(driver.page_source, 'html.parser')
                team2_players = extract_players_from_soup(soup_info_team2)
                
                for p in team2_players:
                    p['batting_stats'] = scrape_player_stats(p['profile_url'])
                    
                info_data["playing_xi"][team2_name] = team2_players
            except Exception as e:
                pass # Silenced
                
    except Exception as e:
        pass # Silenced
        
    return info_data


def scrape_live_data(url):
    """Ye function har bar loop mein chalega Live score nikalne ke liye (Fast Beautifulsoup)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    live_data = {
        "match_info": "",
        "live_score": {},
        "batsmen": [],
        "bowler": {},
        "last_wicket": "",
        "partnership": "",
        "commentary": [],
        "win_predictor": {}
    }
    
    try:
        # Live page load using pure Requests (Super Fast!)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- MATCH INFO ---
        match_title = soup.find(lambda tag: tag.name == "span" and "live" in tag.text.lower())
        if match_title:
            live_data["match_info"] = match_title.text.strip()
            
        # --- LIVE SCORE & CRR ---
        team_name = soup.find('div', class_='team-name')
        score_div = soup.find('div', class_='runs f-runs')
        crr_data = soup.find('span', class_='data')
        status = soup.find('div', class_='final-result')
        
        if team_name and score_div:
            score_spans = score_div.find_all('span')
            if len(score_spans) >= 2:
                live_data["live_score"]["team"] = team_name.text.strip().split()[0]
                live_data["live_score"]["score"] = score_spans[0].text.strip()
                live_data["live_score"]["overs"] = score_spans[1].text.strip()
        if crr_data:
            live_data["live_score"]["crr"] = crr_data.text.strip()
        if status:
            live_data["live_score"]["status"] = status.text.strip()

        # --- LAST BALL RESULT OR EVENT (e.g. 1 run OR Players Entering) ---
        last_ball_text = ""
        result_box = soup.find('div', class_='result-box')
        
        if result_box:
            # Extract all text inside result-box to combine 'font1', 'font2', etc. (e.g. "1 Over")
            last_ball_text = re.sub(r'\s+', ' ', result_box.text.strip())
            
        # Agar result_box me data na ho ya element hi na ho, to sidha font3 check karo (e.g., "Players Entering")
        if not last_ball_text:
            font3 = soup.find('span', class_='font3')
            if font3:
                last_ball_text = re.sub(r'\s+', ' ', font3.text.strip())

        if last_ball_text:
            live_data["live_score"]["last_ball"] = last_ball_text

        # --- LAST WICKET DATA ---
        l_wicket_div = soup.find('div', class_='l-wicket')
        if l_wicket_div:
            # Pura text nikalenge aur "Last Wkt :" ko hata denge
            last_wkt_text = l_wicket_div.text.replace('Last Wkt :', '').strip()
            # Extra spaces ko clean karne ke liye regex ka use
            last_wkt_text = re.sub(r'\s+', ' ', last_wkt_text)
            live_data["last_wicket"] = last_wkt_text

        # --- PARTNERSHIP DATA ---
        p_ship_div = soup.find('div', class_='p-ship')
        if p_ship_div:
            # Pura text nikalenge aur "P'ship :" ko hata denge
            p_ship_text = p_ship_div.text.replace("P'ship :", "").strip()
            # Extra spaces clean
            p_ship_text = re.sub(r'\s+', ' ', p_ship_text)
            live_data["partnership"] = p_ship_text

        # --- BATSMEN & BOWLER DATA ---
        partnerships = soup.find_all('div', class_='batsmen-partnership')
        for p in partnerships:
            imgs = p.find_all('img')
            head_img = imgs[0]['src'] if len(imgs) > 0 else ""
            jersey_img = imgs[1]['src'] if len(imgs) > 1 else ""
            
            career_wrap = p.find('div', class_='batsmen-career-wrapper')
            if not career_wrap: 
                continue
                
            # Add back player_wrap which is required for fetching scores
            player_wrap = career_wrap.find('div', class_='player-wrapper')
                
            # Short name nikalne ke liye batsmen-name class ka use karenge
            name_div = p.find('div', class_='batsmen-name')
            name = name_div.text.strip() if name_div else "Unknown"
            
            sr_wrap = career_wrap.find('div', class_='player-strike-wrapper')
            is_bowler = False
            if sr_wrap and 'Econ' in sr_wrap.text:
                is_bowler = True
                
            if is_bowler:
                score_spans = player_wrap.find('div', class_='p-score').find_all('span') if player_wrap else []
                figures = score_spans[0].text.strip() if len(score_spans) > 0 else ""
                overs = score_spans[1].text.strip() if len(score_spans) > 1 else ""
                
                econ = ""
                if sr_wrap:
                    spans = sr_wrap.find_all('span')
                    if len(spans) > 1:
                        econ = spans[1].text.strip()
                
                live_data["bowler"] = {
                    "name": name,
                    "figures": figures,
                    "overs": overs.replace('(', '').replace(')', ''), 
                    "econ": econ,
                    "head_image_url": head_img,
                    "jersey_image_url": jersey_img
                }
            else:
                score_spans = player_wrap.find('div', class_='p-score').find_all('span') if player_wrap else []
                runs = score_spans[0].text.strip() if len(score_spans) > 0 else ""
                balls = score_spans[1].text.strip() if len(score_spans) > 1 else ""
                
                fours, sixes, sr = "0", "0", "0"
                if sr_wrap:
                    stats = sr_wrap.find_all('div', class_='strike-rate')
                    for stat in stats:
                        text = stat.text
                        if '4s' in text: fours = stat.find_all('span')[1].text.strip()
                        elif '6s' in text: sixes = stat.find_all('span')[1].text.strip()
                        elif 'SR' in text: sr = stat.find_all('span')[1].text.strip()
                            
                live_data["batsmen"].append({
                    "name": name,
                    "runs": runs,
                    "balls": balls.replace('(', '').replace(')', ''),
                    "4s": fours,
                    "6s": sixes,
                    "sr": sr,
                    "head_image_url": head_img,
                    "jersey_image_url": jersey_img
                })

        # --- LATEST COMMENTARY ---
        commentary_cards = soup.find_all('div', class_='cm-b-roundcard')
        for comm in commentary_cards[:3]: 
            over = comm.find('span', class_='cm-b-over')
            runs = comm.find('span', class_='cm-b-ballupdate')
            desc = comm.find('span', class_='cm-b-comment-c1')
            
            if over and runs and desc:
                live_data["commentary"].append({
                    "over": over.text.strip(),
                    "runs": runs.text.strip(),
                    "description": desc.text.strip()
                })

        # --- WIN PREDICTOR (ODDS) ---
        teams = soup.find_all('div', class_='teamNameScreenText')
        percentages = soup.find_all('div', class_='percentageScreenText')
        if len(teams) >= 2 and len(percentages) >= 2:
            live_data["win_predictor"] = {
                teams[0].text.strip(): percentages[0].text.strip(),
                teams[1].text.strip(): percentages[1].text.strip()
            }
            
        return live_data

    except Exception as e:
        return None


def start_loop(link):
    interval = 15 # Har 15 seconds mein data update hoga
    PORT = 8000
    
    print("\n⚙️ Setting up match details, please wait... (It takes a few seconds)")
    
    # --- CHROME OPTIONS (Visible Browser / Non-Headless) ---
    chrome_options = Options()
    # HEADLESS MODE REMOVED HERE
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3") 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    static_info_data = {}
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        driver = webdriver.Chrome(options=chrome_options)
        
    try:
        # Sirf ek baar Selenium se Info fetch karna
        static_info_data = scrape_info_data(driver, link)
    except Exception as e:
        pass
    finally:
        driver.quit() # Selenium ka kaam khatam, browser close kar do!

    # Start Local server in a background thread
    server_thread = threading.Thread(target=start_local_server, args=(PORT,), daemon=True)
    server_thread.start()
    
    # Open default browser
    print(f"\n🌍 Opening Live View in your browser (http://localhost:{PORT})...")
    time.sleep(1) # Thoda delay taaki server properly start ho jaye
    webbrowser.open(f"http://localhost:{PORT}")

    print("\n🚀 Tracking Live Score...")
    print("Press Ctrl+C to stop the application.\n")
    
    try:
        while True:
            # Live data har bar requests se fetch hoga
            live_data = scrape_live_data(link)
            
            if live_data:
                # Dono data (Live + Info) ko combine karna
                final_data = {
                    "match_info": live_data.get("match_info", ""),
                    "toss": static_info_data.get("toss", ""),
                    "team_form": static_info_data.get("team_form", {}),
                    "head_to_head": static_info_data.get("head_to_head", {}),
                    "team_comparison": static_info_data.get("team_comparison", []),
                    "weather": static_info_data.get("weather", {}),
                    "venue_stats": static_info_data.get("venue_stats", {}),
                    "live_score": live_data.get("live_score", {}),
                    "batsmen": live_data.get("batsmen", []),
                    "bowler": live_data.get("bowler", {}),
                    "last_wicket": live_data.get("last_wicket", ""),
                    "partnership": live_data.get("partnership", ""),
                    "commentary": live_data.get("commentary", []),
                    "win_predictor": live_data.get("win_predictor", {}),
                    "playing_xi": static_info_data.get("playing_xi", {})
                }
                
                # File mein directly live_data save karenge
                with open("data.json", "w", encoding="utf-8") as f:
                    json.dump(final_data, f, indent=4, ensure_ascii=False)
                
                # Minimalist clean print
                print(f"✅ Data updated: {time.strftime('%H:%M:%S')}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Loop stopped by user. Server shutting down.")


def main():
    print("==================================================")
    print("      🚀 This software is made by Hemant apps     ")
    print("==================================================")
    print(" 📞 Contact    : +91 9155116696")
    print(" 🌐 Website    : http://hemnthapp.shop")
    print(" 📸 Instagram  : https://www.instagram.com/hemnthkilife")
    print(" ✈️  Telegram   : @Hemnthsoftwaree")
    print("==================================================")
    
    link = input("\n🔗 Enter match link (must end with 'live' or type 'exit' to quit): ").strip()
    
    if link.lower() == 'exit':
        print("Exiting app...")
        return
        
    if link.rstrip('/').lower().endswith("live"):
        start_loop(link)
    else:
        print("❌ Invalid Link! Link ke aakhri mein 'live' likha hona zaroori hai. Please try again.\n")
        main()

if __name__ == "__main__":
    main()
