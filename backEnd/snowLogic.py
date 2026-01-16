#run "pip install requests" in terminal to allow for requests be used. 
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date, timedelta, timezone
import math

def get_forecast_summary(lat, lon):
    #"""Fetch forecast data and return a readable string summary."""
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&forecast_days=5&timezone=America%2FNew_York&temperature_unit=fahrenheit"

    GFS_url = f"https://ensemble-api.open-meteo.com/v1/ensemble?latitude={lat}&longitude={lon}&hourly=snowfall&models=gfs_seamless&forecast_days=5&timezone=America/New_York"
    with ThreadPoolExecutor(max_workers=2) as executor:
        forecast_future = executor.submit(fetch, url)
        gfs_future = executor.submit(fetch, GFS_url)

        data = forecast_future.result()
        GFS_MODEL_data = gfs_future.result()

    temps = data["hourly"]["temperature_2m"]
    times = data["hourly"]["time"] #Need to get the times array to call time later.
    current_time = datetime.now() #gives us the current local time of the user.
    current_hour = current_time.hour 

    summary_24hrs = []
    for i in range(1, 25):
         #this part takes care of the edge case: in case the API decreases time to 24 hours, this will prevent from getting index error.
        next_range_hour = min(current_hour + i, len(temps) - 1)
        next_hour_temp = temps[next_range_hour]

        #this fromisoformat function changes the string into a datetime object. 
        #Needed to change the string to datetime object so we could change the format of date string. 
        forecast_time = datetime.fromisoformat(times[next_range_hour])

        #since the return type of function is a tuple, need to initialize two variables at once.
        snow_chance, snow_amount = get_snowfall_chance_amount_ensemble(next_range_hour, GFS_MODEL_data["hourly"])

        #This .strftime() function allows us to change the format of the datetime object and write it to a string. 
        summary = f"⏱️ Date: {forecast_time.strftime('%Y-%m-%d %H:%M')} | ❄️ Snow chance: {snow_chance:.1f}% | 🌨️ Snow amount: {snow_amount:.2f}cm | 🌡️ Temperature: {next_hour_temp:.1f}°F"
        summary_24hrs.append(summary)
    
    # Return as a joined formatted string
    return "\n".join(summary_24hrs);

#more accurate for snowfall prediction as it accounts for snowfall amounts by ensemble member
#utilizes api from gfs seamless ensembles
def get_snowfall_chance_amount_ensemble(next_hour, data):
    nextHourSnowCount = 0
    nextHourSnowAmount = 0

    #since there are 30 members given in the currently used data, just loop 30 times.
    for i in range(1, 31):
        currentMember = f"snowfall_member{i:02d}"
        current_data = data[currentMember][next_hour]
        #for now, the loop only predicts for the next hour. If we want more hours like 24, then I can modify the logic to do so.
        if (current_data != 0):
            nextHourSnowCount+=1
            nextHourSnowAmount+=current_data
    
    #get the average percent of snowing chance
    snowPercent = (nextHourSnowCount/30)*100

    finalSnowAmount = 0
    if (nextHourSnowCount != 0): #this statement is required to prevent division by 0 error.
        finalSnowAmount = nextHourSnowAmount/nextHourSnowCount
    
    return (snowPercent, finalSnowAmount)
#     GEM_url = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=gem_global&forecast_days=7&timezone=America%2FYellowknife"
#     ICON_MODEL_data = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=icon_seamless&forecast_days=7&timezone=America%2FYellowknife"
#    #precipAndMake =

def fetch(url):
    return requests.get(url, timeout=10).json()

def get_nws_alerts(lat, lon):
    url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
    r = requests.get(url)
    r.raise_for_status()
    alerts_json = r.json()  # JSON with alert features
    results = ""

    for alert in alerts_json.get("features", []):
        props = alert.get("properties", {})

        event = props.get("event", "Unknown Alert")
        ends = props.get("ends") or props.get("expires")
        #only looking for winter related weather alerts
        if event == "Winter Weather Advisory" or event == "Winter Storm Warning" or event == "Winter Storm Watch" or event == "Blizzard Warning" or event == "Ice Storm Warning":
            # Convert to readable datetime
            if ends:
                ends_dt = datetime.fromisoformat(ends)
                ends_str = ends_dt.strftime("%Y-%m-%d %I:%M %p")
            else:
                ends_str = "Unknown"
            results += "Alert: " + event + " Valid Until " + ends_str      
    return results
from datetime import datetime, date, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

def schoolPredictionForDay(lat, lon, days=5, return_debug=True):
    """
    More-sensitive, robust school closure predictor.
    Keeps same external helpers: fetch, get_snowfall_chance_amount_ensemble, get_nws_alerts.
    Returns {"cancel":..., "delay":..., "debug":...}
    """

    # ---------- Tunables (more sensitive than before) ----------
    TH_P2_CM = 2.5    # ~1"
    TH_P4_CM = 5.0    # ~2"
    TH_P6_CM = 10.0   # ~4"

    W_OVERNIGHT = 1.0
    W_MORNING = 2.0
    W_AFTERNOON = 0.35

    EVENING_TO_NEXT_MORNING_THRESHOLD_CM = 2.0
    INTENSITY_RATE_CM_PER_HR = 0.25   # treat lower intensity as impactful
    BLIZZARD_WIND_MS = 12.0          # lower wind threshold to be more sensitive
    FUTURE_CAP_HOURS = 36

    TEMP_SLUSH_LOW = -2.0
    TEMP_SLUSH_HIGH = 2.0
    TEMP_SLUSH_MULT = 1.12

    # ---------- Endpoints ----------
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}"
           f"&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m"
           f"&forecast_days={days}&timezone=America%2FNew_York")
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    archive_url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}"
                   f"&longitude={lon}&hourly=snow_depth"
                   f"&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
                   f"&timezone=America%2FNew_York")
    GFS_url = (f"https://ensemble-api.open-meteo.com/v1/ensemble?latitude={lat}"
               f"&longitude={lon}&hourly=snowfall&models=gfs_seamless"
               f"&forecast_days={days}&timezone=America%2FNew_York")
    nws_point_url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"

    # ---------- Fetch ----------
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            f1 = executor.submit(fetch, url)
            f2 = executor.submit(fetch, GFS_url)
            f3 = executor.submit(fetch, archive_url)
            f4 = executor.submit(fetch, nws_point_url)
            data = f1.result() or {}
            GFS_MODEL_data = f2.result() or {}
            archive_data = f3.result() or {}
            nws_data = f4.result() or {}
    except Exception:
        return {
            "cancel": {f"day{i}": "very unlikely" for i in range(1, days+1)},
            "delay":  {f"day{i}": "very unlikely" for i in range(1, days+1)},
            "debug": {}
        }

    # ---------- Helpers to extract ensembles robustly ----------
    def _to_cm(v):
        try:
            vv = float(v or 0.0)
        except Exception:
            return 0.0
        return (vv / 10.0) if vv > 5.0 else vv

    def _extract_ensemble_members(GFS_MODEL_data, length):
        members = []
        hourly_obj = (GFS_MODEL_data.get("hourly") if isinstance(GFS_MODEL_data, dict) else {}) or {}

        member_keys = [k for k in hourly_obj.keys() if "snow" in k.lower() and ("member" in k.lower() or "mbr" in k.lower())]
        if member_keys:
            for k in sorted(member_keys):
                arr = hourly_obj.get(k, []) or []
                hourly_cm = [_to_cm(x) for x in arr]
                hourly_cm = (hourly_cm + [0.0]*length)[:length]
                members.append({"hourly_snow_cm": hourly_cm})
            return members

        if isinstance(GFS_MODEL_data, dict) and "members" in GFS_MODEL_data and isinstance(GFS_MODEL_data["members"], list):
            for mem in GFS_MODEL_data["members"]:
                hv = (mem.get("hourly", {}) or {}).get("snowfall", []) or []
                hourly_cm = [_to_cm(x) for x in hv]
                hourly_cm = (hourly_cm + [0.0]*length)[:length]
                members.append({"hourly_snow_cm": hourly_cm})
            if members:
                return members

        sf = hourly_obj.get("snowfall")
        if isinstance(sf, list) and sf:
            if any(isinstance(x, list) for x in sf):
                for member_arr in sf:
                    hourly_cm = [_to_cm(x) for x in member_arr]
                    hourly_cm = (hourly_cm + [0.0]*length)[:length]
                    members.append({"hourly_snow_cm": hourly_cm})
                return members
            else:
                hourly_cm = [_to_cm(x) for x in sf]
                hourly_cm = (hourly_cm + [0.0]*length)[:length]
                return [{"hourly_snow_cm": hourly_cm}]

        for k,v in hourly_obj.items():
            if "snow" in k.lower() and isinstance(v, list):
                hourly_cm = [_to_cm(x) for x in v]
                hourly_cm = (hourly_cm + [0.0]*length)[:length]
                return [{"hourly_snow_cm": hourly_cm}]

        return [{"hourly_snow_cm": [0.0]*length}]

    # ---------- Parse forecast arrays ----------
    hourly = data.get("hourly", {}) or {}
    times = hourly.get("time", []) or []
    temps = hourly.get("temperature_2m", []) or []
    precip = hourly.get("precipitation", []) or []
    winds = hourly.get("windspeed_10m", []) or []

    time_datetimes = []
    for t in times:
        try:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
        except Exception:
            try:
                dt = datetime.fromisoformat(t)
            except Exception:
                continue
        time_datetimes.append(dt)
    times_len = len(time_datetimes)

    ensemble_members = _extract_ensemble_members(GFS_MODEL_data, times_len) or [{"hourly_snow_cm":[0.0]*times_len}]

    # ---------- Ensemble helpers ----------
    def probability_ge_threshold(ensemble_members, s, e, threshold_cm):
        if not ensemble_members:
            return 0.0
        hits = 0
        for m in ensemble_members:
            arr = m["hourly_snow_cm"]
            if s >= len(arr):
                total = 0.0
            else:
                total = sum(arr[max(0,s):min(len(arr), e)])
            if total >= threshold_cm:
                hits += 1
        return hits / len(ensemble_members)

    def ensemble_mean_sum(ensemble_members, s, e):
        total = 0.0
        count = 0
        for m in ensemble_members:
            arr = m["hourly_snow_cm"]
            if s >= len(arr):
                val = 0.0
            else:
                val = sum(arr[max(0,s):min(len(arr), e)])
            total += val
            count += 1
        return (total / count) if count else 0.0

    def intensity_probability(ensemble_members, s, e, rate_cm_per_hr):
        if not ensemble_members:
            return 0.0
        hits = 0
        for m in ensemble_members:
            arr = m["hourly_snow_cm"]
            if s >= len(arr):
                mm = 0.0
            else:
                window = arr[max(0,s):min(len(arr), e)]
                mm = max(window) if window else 0.0
            if mm >= rate_cm_per_hr:
                hits += 1
        return hits / len(ensemble_members)

    # ---------- Align start_idx ----------
    start_idx = 0
    try:
        now_utc = datetime.now(timezone.utc)
        if time_datetimes and time_datetimes[0].tzinfo is not None:
            now_local = now_utc.astimezone(time_datetimes[0].tzinfo)
        else:
            now_local = datetime.now()
        now_floor = now_local.replace(minute=0, second=0, microsecond=0)
        for idx, dt in enumerate(time_datetimes):
            if dt >= now_floor:
                start_idx = idx
                break
    except Exception:
        start_idx = 0

    # ---------- Current snow depth ----------
    snow_depths = (archive_data.get("hourly", {}) or {}).get("snow_depth", []) if isinstance(archive_data, dict) else []
    try:
        current_snow_depth = float(snow_depths[-1] or 0.0) if snow_depths else 0.0
    except Exception:
        current_snow_depth = 0.0

    # ---------- NWS alerts ----------
    nws_features = []
    try:
        if isinstance(nws_data, dict):
            nws_features = nws_data.get("features", []) or []
    except Exception:
        nws_features = []

    def alerts_overlap_day(nws_features, day_start_dt, day_end_dt):
        severe_on_day = False
        advisory_on_day = False
        for feat in nws_features:
            try:
                props = feat.get("properties", {}) if isinstance(feat, dict) else {}
                eff = None
                ends = None
                try:
                    eff = datetime.fromisoformat((props.get("effective") or "").replace("Z", "+00:00"))
                except Exception:
                    eff = None
                try:
                    ends = datetime.fromisoformat((props.get("ends") or "").replace("Z", "+00:00"))
                except Exception:
                    ends = None
                if eff is None and ends is None:
                    continue
                if eff is None:
                    eff = datetime.min.replace(tzinfo=timezone.utc)
                if ends is None:
                    ends = datetime.max.replace(tzinfo=timezone.utc)
                if not (ends <= day_start_dt or eff >= day_end_dt):
                    ev = (props.get("event") or "").lower()
                    if "warning" in ev and ("winter" in ev or "blizzard" in ev or "ice" in ev):
                        severe_on_day = True
                    if "advisory" in ev or "watch" in ev:
                        advisory_on_day = True
            except Exception:
                continue
        return severe_on_day, advisory_on_day

    # ---------- Decision loops ----------
    cancel_out = {}
    delay_out = {}
    debug = {}
    hours_per_day = 24

    for day in range(days):
        day_start = start_idx + day * hours_per_day
        day_end = day_start + hours_per_day

        if day_start < len(time_datetimes):
            day_start_dt = time_datetimes[day_start]
        else:
            day_start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day)
        if (day_end - 1) < len(time_datetimes):
            day_end_dt = time_datetimes[day_end - 1] + timedelta(hours=1)
        else:
            day_end_dt = day_start_dt + timedelta(hours=24)

        morning_s = day_start + 6
        morning_e = day_start + 9
        decision_s = day_start - 6
        decision_e = day_start + 18

        # ensemble metrics
        day_mean_ens_cm = ensemble_mean_sum(ensemble_members, max(0, day_start), max(0, day_end))
        morning_mean_ens_cm = ensemble_mean_sum(ensemble_members, max(0, morning_s), max(0, morning_e))
        P2 = probability_ge_threshold(ensemble_members, max(0, decision_s), max(0, decision_e), TH_P2_CM)
        P4 = probability_ge_threshold(ensemble_members, max(0, decision_s), max(0, decision_e), TH_P4_CM)
        P6 = probability_ge_threshold(ensemble_members, max(0, decision_s), max(0, decision_e), TH_P6_CM)
        intensity_prob = intensity_probability(ensemble_members, max(0, morning_s), max(0, morning_e), INTENSITY_RATE_CM_PER_HR)

        # deterministic arrays summary and per-hour ensemble "chance" and "amount"
        total_precip_mm = 0.0
        max_wind = 0.0
        temps_for_mean = []
        max_hourly_ens = 0.0
        max_hourly_chance = 0.0
        for hr_idx in range(day_start, min(day_end, len(time_datetimes))):
            if hr_idx < len(precip):
                total_precip_mm += precip[hr_idx] or 0.0
            if hr_idx < len(winds):
                try:
                    max_wind = max(max_wind, float(winds[hr_idx] or 0.0))
                except Exception:
                    pass
            if hr_idx < len(temps):
                temps_for_mean.append(temps[hr_idx])
            try:
                snow_chance, snow_amount = get_snowfall_chance_amount_ensemble(hr_idx, GFS_MODEL_data.get("hourly", {}))
            except Exception:
                snow_chance, snow_amount = 0.0, 0.0
            max_hourly_ens = max(max_hourly_ens, snow_amount or 0.0)
            max_hourly_chance = max(max_hourly_chance, snow_chance or 0.0)

        mean_temp_c = (sum(temps_for_mean) / len(temps_for_mean)) if temps_for_mean else None

        severe_on_day, advisory_on_day = alerts_overlap_day(nws_features, day_start_dt, day_end_dt)

        try:
            now_local = datetime.now(timezone.utc).astimezone(day_start_dt.tzinfo) if day_start_dt.tzinfo else datetime.now()
            hours_until_event = max(0.0, (day_start_dt - now_local).total_seconds() / 3600.0)
        except Exception:
            hours_until_event = 0.0

        if hours_until_event > FUTURE_CAP_HOURS:
            P6 = min(P6, 0.30)
            P4 = min(P4, 0.50)
            P2 = min(P2, 0.75)

        # ---------- Scoring ----------
        # stronger emphasis on P4/P6 and ensemble mean
        prob_component = (0.6 * P6 + 0.3 * P4 + 0.1 * P2) * 100.0
        impact_component = day_mean_ens_cm * 18.0
        intensity_component = intensity_prob * 20.0
        morning_emphasis = (W_MORNING * morning_mean_ens_cm)

        temp_component = 0.0
        if mean_temp_c is not None and TEMP_SLUSH_LOW <= mean_temp_c <= TEMP_SLUSH_HIGH:
            temp_component = 8.0
            impact_component *= TEMP_SLUSH_MULT

        # carryover from snowpack
        carryover_bonus = 0.0
        if current_snow_depth := ( (archive_data.get("hourly", {}) or {}).get("snow_depth", [])[-1] if (archive_data.get("hourly", {}) or {}).get("snow_depth", []) else 0.0 ):
            try:
                current_snow_depth = float(current_snow_depth or 0.0)
            except Exception:
                current_snow_depth = 0.0
        if current_snow_depth >= 12.0:
            carryover_bonus += min(22.0, (current_snow_depth - 8.0) * 1.5)
        elif current_snow_depth >= 6.0:
            carryover_bonus += min(12.0, (current_snow_depth - 4.0) * 1.0)

        # wind
        wind_bonus = 0.0
        wind_vals = []
        for wi in range(max(0, morning_s), min(len(winds), morning_e)):
            try:
                wind_vals.append(winds[wi])
            except Exception:
                pass
        wind_mean = (sum(wind_vals) / len(wind_vals)) if wind_vals else 0.0
        if wind_mean >= BLIZZARD_WIND_MS:
            wind_bonus = 14.0

        # alert bonuses (more aggressive but still require at least some evidence to go full)
        alert_bonus = 0.0
        if severe_on_day:
            if (P2 >= 0.12) or (day_mean_ens_cm >= 2.0) or (max_hourly_chance >= 20.0) or (current_snow_depth >= 4.0):
                alert_bonus += 36.0
            else:
                alert_bonus += 16.0
        if advisory_on_day:
            if (P2 >= 0.10) or (day_mean_ens_cm >= 1.0) or (current_snow_depth >= 3.0):
                alert_bonus += 10.0
            else:
                alert_bonus += 4.0

        # morning precip deterministic
        morning_precip_mm = 0.0
        for hr_idx in range(max(morning_s, day_start), min(morning_e, day_end, len(precip))):
            morning_precip_mm += precip[hr_idx] or 0.0
        morning_precip_bonus = 0.0
        if morning_precip_mm >= 3.0:
            morning_precip_bonus = 8.0
        elif morning_precip_mm >= 1.5:
            morning_precip_bonus = 4.0

        # per-hour ensemble chance direct influence (max_hourly_chance is 0-100)
        hourly_chance_bonus = (max_hourly_chance * 0.5)  # e.g., 80% hourly chance -> +40 points

        # assemble score
        score = prob_component + impact_component + intensity_component + temp_component + carryover_bonus + wind_bonus + alert_bonus + morning_precip_bonus + hourly_chance_bonus

        # hard bumps (if there's a clear per-hour signal)
        if max_hourly_chance >= 80.0 and max_hourly_ens >= 1.5:
            score = max(score, 60.0)
        if (morning_mean_ens_cm >= 2.5) or (day_mean_ens_cm >= 4.0):
            score = max(score, 55.0)
        if severe_on_day and (P2 >= 0.08 or max_hourly_chance >= 25.0):
            score = max(score, 58.0)

        score = max(0.0, min(100.0, score))

        # category mapping
        def cancel_from_score(s):
            if s >= 88:
                return "almost guaranteed"
            if s >= 70:
                return "likely"
            if s >= 50:
                return "possible"
            if s >= 30:
                return "unlikely"
            return "very unlikely"

        def delay_from_score(s, morning_emphasis, intensity_prob):
            dscore = s + (morning_emphasis * 6.0) + (intensity_prob * 12.0)
            if dscore >= 88:
                return "almost guaranteed"
            if dscore >= 70:
                return "likely"
            if dscore >= 52:
                return "possible"
            if dscore >= 30:
                return "unlikely"
            return "very unlikely"

        cancel_cat = cancel_from_score(score)
        delay_cat = delay_from_score(score, morning_emphasis, intensity_prob)

        # safety clamping: if alert but no evidence, don't go to almost guaranteed
        if severe_on_day and cancel_cat == "almost guaranteed" and (P6 < 0.35 and day_mean_ens_cm < 3.0 and max_hourly_chance < 30.0 and current_snow_depth < 6.0):
            cancel_cat = "likely"

        # override for very large snowpack
        if current_snow_depth >= 25.0:
            cancel_cat = "almost guaranteed"
            delay_cat = "almost guaranteed"
        elif current_snow_depth >= 15.0:
            cancel_cat = max(cancel_cat, "likely", key=lambda x: ["very unlikely","unlikely","possible","likely","almost guaranteed"].index(x))
            delay_cat = max(delay_cat, "likely", key=lambda x: ["very unlikely","unlikely","possible","likely","almost guaranteed"].index(x))

        cancel_out[f"day{day+1}"] = cancel_cat
        delay_out[f"day{day+1}"] = delay_cat

        debug[f"day{day+1}"] = {
            "score": round(score,2),
            "P2": round(P2,3), "P4": round(P4,3), "P6": round(P6,3),
            "day_mean_ens_cm": round(day_mean_ens_cm,2),
            "morning_mean_ens_cm": round(morning_mean_ens_cm,2),
            "intensity_prob": round(intensity_prob,3),
            "mean_temp_c": (round(mean_temp_c,2) if mean_temp_c is not None else None),
            "current_snow_depth_cm": round(current_snow_depth,2),
            "severe_on_day": bool(severe_on_day),
            "advisory_on_day": bool(advisory_on_day),
            "morning_precip_mm": round(morning_precip_mm,2),
            "wind_mean": round(wind_mean,2),
            "max_hourly_ens": round(max_hourly_ens,2),
            "max_hourly_chance": round(max_hourly_chance,2)
        }

    out = {"cancel": cancel_out, "delay": delay_out}
    if return_debug:
        out["debug"] = debug
    return out
