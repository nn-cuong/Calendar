#!/usr/bin/env python3
import os
import sys
import datetime
import json
from lunar import convertSolar2Lunar

# Add local bundled vendor
VENDOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.exists(VENDOR_PATH):
    sys.path.insert(0, VENDOR_PATH)

os.environ["PYSDL2_DLL_PATH"] = "/usr/trimui/lib"

try:
    import sdl2
    import sdl2.ext
    import sdl2.sdlttf as sdlttf
except ImportError as e:
    sys.stderr.write("Cannot load SDL2. Error: " + str(e))
    sys.exit(1)

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font.ttf")
SAVES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves.json")

# Themes
CALENDAR_THEMES = [
    {
        "name": "Original",
        "bg": sdl2.ext.Color(245, 241, 230),           # #F5F1E6
        "text": sdl2.SDL_Color(51, 48, 43, 255),       # #33302B
        "text_dim": sdl2.SDL_Color(111, 106, 96, 255), # #6F6A60
        "header": sdl2.SDL_Color(48, 46, 42, 255),     # #302E2A
        "sunday": sdl2.SDL_Color(182, 92, 92, 255),    # #B65C5C
        "saturday": sdl2.SDL_Color(88, 112, 128, 255), # #587080
        "lunar": sdl2.SDL_Color(107, 91, 149, 255),    # #6B5B95
        "today_border": sdl2.ext.Color(217, 184, 108), # #D9B86C
        "sel_border": sdl2.ext.Color(102, 137, 181),   # #6689B5
        "sel_bg": sdl2.ext.Color(229, 235, 241),       # #E5EBF1
        "grid": sdl2.ext.Color(221, 215, 200),         # #DDD7C8
    },
    {
        "name": "Midnight",
        "bg": sdl2.ext.Color(18, 22, 29),              # #12161D
        "text": sdl2.SDL_Color(227, 232, 239, 255),    # #E3E8EF
        "text_dim": sdl2.SDL_Color(143, 154, 170, 255),# #8F9AAA
        "header": sdl2.SDL_Color(143, 154, 170, 255),  # #8F9AAA
        "sunday": sdl2.SDL_Color(169, 160, 184, 255),  # #A9A0B8
        "saturday": sdl2.SDL_Color(169, 160, 184, 255),# #A9A0B8
        "lunar": sdl2.SDL_Color(127, 167, 216, 255),   # #7FA7D8
        "today_border": sdl2.ext.Color(76, 113, 159),  # #4C719F
        "sel_border": sdl2.ext.Color(127, 167, 216),   # #7FA7D8
        "sel_bg": sdl2.ext.Color(38, 56, 77),          # #26384D
        "grid": sdl2.ext.Color(52, 66, 82),            # #344252
    },
    {
        "name": "Warm Paper",
        "bg": sdl2.ext.Color(243, 235, 217),           # #F3EBD9
        "text": sdl2.SDL_Color(64, 57, 47, 255),       # #40392F
        "text_dim": sdl2.SDL_Color(136, 123, 104, 255),# #887B68
        "header": sdl2.SDL_Color(136, 123, 104, 255),  # #887B68
        "sunday": sdl2.SDL_Color(154, 111, 98, 255),   # #9A6F62
        "saturday": sdl2.SDL_Color(154, 111, 98, 255), # #9A6F62
        "lunar": sdl2.SDL_Color(168, 120, 63, 255),    # #A8783F
        "today_border": sdl2.ext.Color(198, 154, 82),  # #C69A52
        "sel_border": sdl2.ext.Color(168, 120, 63),    # #A8783F
        "sel_bg": sdl2.ext.Color(228, 208, 165),       # #E4D0A5
        "grid": sdl2.ext.Color(210, 192, 157),         # #D2C09D
    },
    {
        "name": "Forest",
        "bg": sdl2.ext.Color(24, 32, 27),              # #18201B
        "text": sdl2.SDL_Color(217, 226, 213, 255),    # #D9E2D5
        "text_dim": sdl2.SDL_Color(158, 173, 159, 255),# #9EAD9F
        "header": sdl2.SDL_Color(158, 173, 159, 255),  # #9EAD9F
        "sunday": sdl2.SDL_Color(176, 169, 154, 255),  # #B0A99A
        "saturday": sdl2.SDL_Color(176, 169, 154, 255),# #B0A99A
        "lunar": sdl2.SDL_Color(168, 184, 138, 255),   # #A8B88A
        "today_border": sdl2.ext.Color(95, 125, 98),   # #5F7D62
        "sel_border": sdl2.ext.Color(168, 184, 138),   # #A8B88A
        "sel_bg": sdl2.ext.Color(41, 54, 45),          # #29362D
        "grid": sdl2.ext.Color(73, 98, 79),            # #49624F
    }
]

def load_theme_idx():
    try:
        if os.path.exists(SAVES_FILE):
            with open(SAVES_FILE, 'r') as f:
                saves = json.load(f)
                return int(saves.get("theme_idx", 0)) % len(CALENDAR_THEMES)
    except:
        pass
    return 0

def write_theme_idx(theme_idx):
    try:
        saves = {}
        if os.path.exists(SAVES_FILE):
            with open(SAVES_FILE, 'r') as f:
                saves = json.load(f)
        saves["theme_idx"] = theme_idx % len(CALENDAR_THEMES)
        with open(SAVES_FILE, 'w') as f:
            json.dump(saves, f)
    except:
        pass

MODE_SOLAR = 0
MODE_LUNAR = 1

def draw_border(renderer, x, y, w, h, border_color, bg_color, thickness=3):
    # Outer (Border)
    renderer.fill((x, y, w, h), border_color)
    # Inner (Background)
    ix, iy = x + thickness, y + thickness
    iw, ih = w - 2 * thickness, h - 2 * thickness
    if iw > 0 and ih > 0:
        renderer.fill((ix, iy, iw, ih), bg_color)

def main():
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER)
    sdlttf.TTF_Init()

    num_joysticks = sdl2.SDL_NumJoysticks()
    controllers = []
    for i in range(num_joysticks):
        if sdl2.SDL_IsGameController(i):
            c = sdl2.SDL_GameControllerOpen(i)
            if c:
                controllers.append(c)

    window = sdl2.ext.Window("Calendar", size=(1024, 768), flags=sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
    window.show()
    renderer = sdl2.ext.Renderer(window)

    font_path = FONT_PATH.encode('utf-8')
    if os.path.exists(FONT_PATH):
        font_large = sdlttf.TTF_OpenFont(font_path, 48)
        font_medium = sdlttf.TTF_OpenFont(font_path, 32)
        font_small = sdlttf.TTF_OpenFont(font_path, 24)
    else:
        sys.exit(1)

    def render_text(text, font, color):
        tsurf = sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
        if tsurf:
            ttex = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, tsurf)
            w, h = tsurf.contents.w, tsurf.contents.h
            sdl2.SDL_FreeSurface(tsurf)
            return ttex, w, h
        return None, 0, 0

    def get_days_in_month(year, month):
        return 29 if month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else (28 if month == 2 else (30 if month in (4, 6, 9, 11) else 31))

    def get_month_calendar(year, month):
        first_day = datetime.date(year, month, 1).weekday()
        days_in_m = get_days_in_month(year, month)
        cal = []
        curr_day = 1
        week = [0] * 7
        for i in range(first_day, 7):
            week[i] = curr_day
            curr_day += 1
        cal.append(week)
        while curr_day <= days_in_m:
            week = [0] * 7
            for i in range(7):
                if curr_day <= days_in_m:
                    week[i] = curr_day
                    curr_day += 1
            cal.append(week)
        return cal

    now = datetime.datetime.now()
    cur_year = now.year
    cur_month = now.month
    cursor_day = now.day
    
    view_mode = MODE_SOLAR
    theme_idx = load_theme_idx()

    weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    
    running = True
    l2_pressed = False
    r2_pressed = False
    show_quit_confirm = False

    prev_axis_up = False
    prev_axis_down = False
    prev_axis_left = False
    prev_axis_right = False
    axis_timer_v = 0
    axis_timer_h = 0
    dpad_up_held = False
    dpad_down_held = False
    dpad_left_held = False
    dpad_right_held = False
    dpad_timer_v = 0
    dpad_timer_h = 0

    def nav_up():
        nonlocal cursor_day
        cursor_day = max(1, cursor_day - 7)

    def nav_down():
        nonlocal cursor_day
        cursor_day = min(get_days_in_month(cur_year, cur_month), cursor_day + 7)

    def nav_left():
        nonlocal cursor_day
        cursor_day = max(1, cursor_day - 1)

    def nav_right():
        nonlocal cursor_day
        cursor_day = min(get_days_in_month(cur_year, cur_month), cursor_day + 1)

    while running:
        needs_redraw = True
        
        # Poll Joystick Axes
        axis_up = False
        axis_down = False
        axis_left = False
        axis_right = False
        for c in controllers:
            lx = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_LEFTX)
            ly = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_LEFTY)
            rx = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_RIGHTX)
            ry = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_RIGHTY)
            ax = lx if abs(lx) >= abs(rx) else rx
            ay = ly if abs(ly) >= abs(ry) else ry
            if ay < -15000: axis_up = True
            elif ay > 15000: axis_down = True
            if ax < -15000: axis_left = True
            elif ax > 15000: axis_right = True

        if not show_quit_confirm:
            if axis_up:
                if not prev_axis_up:
                    nav_up()
                    axis_timer_v = 0
                else:
                    axis_timer_v += 1
                    if axis_timer_v > 15 and axis_timer_v % 4 == 0:
                        nav_up()
            elif axis_down:
                if not prev_axis_down:
                    nav_down()
                    axis_timer_v = 0
                else:
                    axis_timer_v += 1
                    if axis_timer_v > 15 and axis_timer_v % 4 == 0:
                        nav_down()
            else:
                axis_timer_v = 0

            if axis_left:
                if not prev_axis_left:
                    nav_left()
                    axis_timer_h = 0
                else:
                    axis_timer_h += 1
                    if axis_timer_h > 15 and axis_timer_h % 4 == 0:
                        nav_left()
            elif axis_right:
                if not prev_axis_right:
                    nav_right()
                    axis_timer_h = 0
                else:
                    axis_timer_h += 1
                    if axis_timer_h > 15 and axis_timer_h % 4 == 0:
                        nav_right()
            else:
                axis_timer_h = 0

            if dpad_up_held:
                dpad_timer_v += 1
                if dpad_timer_v > 15 and dpad_timer_v % 4 == 0:
                    nav_up()
            elif dpad_down_held:
                dpad_timer_v += 1
                if dpad_timer_v > 15 and dpad_timer_v % 4 == 0:
                    nav_down()
            else:
                dpad_timer_v = 0

            if dpad_left_held:
                dpad_timer_h += 1
                if dpad_timer_h > 15 and dpad_timer_h % 4 == 0:
                    nav_left()
            elif dpad_right_held:
                dpad_timer_h += 1
                if dpad_timer_h > 15 and dpad_timer_h % 4 == 0:
                    nav_right()
            else:
                dpad_timer_h = 0

        prev_axis_up = axis_up
        prev_axis_down = axis_down
        prev_axis_left = axis_left
        prev_axis_right = axis_right
        
        events = sdl2.ext.get_events()
        if len(events) > 0:
            needs_redraw = True
            
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                sym = event.key.keysym.sym
                if sym == sdl2.SDLK_x:
                    view_mode = MODE_LUNAR if view_mode == MODE_SOLAR else MODE_SOLAR
                elif sym == sdl2.SDLK_y:
                    theme_idx = (theme_idx + 1) % len(CALENDAR_THEMES)
                    write_theme_idx(theme_idx)
            elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                btn = event.cbutton.button
                if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: dpad_up_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: dpad_down_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: dpad_left_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: dpad_right_held = False
            elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                btn = event.cbutton.button
                if show_quit_confirm:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A - Confirm
                        running = False
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B - Cancel
                        show_quit_confirm = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_START:
                    show_quit_confirm = True
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER:
                    cur_month -= 1
                    if cur_month < 1:
                        cur_month = 12
                        cur_year -= 1
                    cursor_day = min(cursor_day, get_days_in_month(cur_year, cur_month))
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
                    cur_month += 1
                    if cur_month > 12:
                        cur_month = 1
                        cur_year += 1
                    cursor_day = min(cursor_day, get_days_in_month(cur_year, cur_month))
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                    dpad_up_held = True
                    dpad_timer_v = 0
                    nav_up()
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                    dpad_down_held = True
                    dpad_timer_v = 0
                    nav_down()
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                    dpad_left_held = True
                    dpad_timer_h = 0
                    nav_left()
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                    dpad_right_held = True
                    dpad_timer_h = 0
                    nav_right()
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_B:
                    now_t = datetime.datetime.now()
                    cur_year = now_t.year
                    cur_month = now_t.month
                    cursor_day = now_t.day
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_Y: # Physical X on TrimUI - Solar / Lunar
                    view_mode = MODE_LUNAR if view_mode == MODE_SOLAR else MODE_SOLAR
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_X: # Physical Y on TrimUI - Theme Switch
                    theme_idx = (theme_idx + 1) % len(CALENDAR_THEMES)
                    write_theme_idx(theme_idx)
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: # Fallback L2 on some TrimUI CFW
                    cur_year -= 1
                    cursor_day = min(cursor_day, get_days_in_month(cur_year, cur_month))
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: # Fallback R2 on some TrimUI CFW
                    cur_year += 1
                    cursor_day = min(cursor_day, get_days_in_month(cur_year, cur_month))
            elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                axis = event.caxis.axis
                val = event.caxis.value
                if axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT:
                    if val > 16000 and not l2_pressed:
                        l2_pressed = True
                        cur_year -= 1
                        cursor_day = min(cursor_day, get_days_in_month(cur_year, cur_month))
                    elif val <= 16000:
                        l2_pressed = False
                elif axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT:
                    if val > 16000 and not r2_pressed:
                        r2_pressed = True
                        cur_year += 1
                        cursor_day = min(cursor_day, get_days_in_month(cur_year, cur_month))
                    elif val <= 16000:
                        r2_pressed = False

        if needs_redraw:
            theme = CALENDAR_THEMES[theme_idx]
            renderer.clear(theme["bg"])
            w_w, w_h = 1024, 768
            
            # Draw Header
            if view_mode == MODE_SOLAR:
                header = f"SOLAR {cursor_day:02d}-{cur_month:02d}-{cur_year:04d}"
                header_color = theme["text"]
                sdlttf.TTF_SetFontStyle(font_large, sdlttf.TTF_STYLE_BOLD)
            else:
                try:
                    ld, lm, ly, _ = convertSolar2Lunar(cursor_day, cur_month, cur_year)
                    header = f"LUNAR {ld:02d}-{lm:02d}-{ly:04d}"
                except Exception:
                    header = f"LUNAR {cursor_day:02d}-{cur_month:02d}-{cur_year:04d}"
                header_color = theme["lunar"]
                sdlttf.TTF_SetFontStyle(font_large, sdlttf.TTF_STYLE_BOLD)
                
            tex, tw, th = render_text(header, font_large, header_color)
            sdlttf.TTF_SetFontStyle(font_large, sdlttf.TTF_STYLE_NORMAL)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(w_w//2 - tw//2, 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
            # Draw Weekdays
            cell_w = 120
            cell_h = 80
            start_x = (w_w - (cell_w * 7)) // 2
            start_y = 120
            
            for i, wd in enumerate(weekdays):
                color = theme["sunday"] if i == 6 else (theme["saturday"] if i == 5 else theme["header"])
                tex, tw, th = render_text(wd, font_medium, color)
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(start_x + i * cell_w + cell_w//2 - tw//2, start_y + 10, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                    
            # Draw Days
            start_y += 70
            cal = get_month_calendar(cur_year, cur_month)
            
            # Draw Grid
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, theme["grid"].r, theme["grid"].g, theme["grid"].b, 255)
            grid_w = cell_w * 7
            grid_h = cell_h * len(cal)
            for r in range(len(cal) + 1):
                y = start_y + r * cell_h - 5
                sdl2.SDL_RenderDrawLine(renderer.sdlrenderer, start_x, y, start_x + grid_w, y)
            for c in range(8):
                x = start_x + c * cell_w
                sdl2.SDL_RenderDrawLine(renderer.sdlrenderer, x, start_y - 5, x, start_y + grid_h - 5)
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_NONE)
            
            today = datetime.datetime.now()
            
            for r, week in enumerate(cal):
                for c, day in enumerate(week):
                    if day != 0:
                        bx = start_x + c * cell_w
                        by = start_y + r * cell_h
                        
                        is_today = (day == today.day and cur_month == today.month and cur_year == today.year)
                        if is_today:
                            rx, ry = bx + 1, by - 4
                            rw, rh = cell_w - 2, cell_h - 2
                            draw_border(renderer, rx, ry, rw, rh, theme["today_border"], theme["bg"], thickness=3)
                            
                        is_cursor = (day == cursor_day)
                        if is_cursor:
                            # Draw selected border around cursor
                            rx, ry = bx + 1, by - 4
                            rw, rh = cell_w - 2, cell_h - 2
                            draw_border(renderer, rx, ry, rw, rh, theme["sel_border"], theme["sel_bg"], thickness=2)
                        
                        # Convert to Lunar
                        try:
                            ld, lm, ly, lleap = convertSolar2Lunar(day, cur_month, cur_year)
                            lunar_str = f"{ld}/{lm}"
                            if ld == 1: lunar_str = f"{ld}/{lm}"
                            else: lunar_str = f"{ld}"
                        except Exception:
                            lunar_str = "--"
                        
                        if view_mode == MODE_SOLAR:
                            prim_str = str(day)
                            sec_str = lunar_str
                            prim_color = theme["sunday"] if c == 6 else (theme["saturday"] if c == 5 else theme["text"])
                            sec_color = theme["lunar"]
                        else:
                            prim_str = lunar_str
                            sec_str = str(day)
                            prim_color = theme["lunar"]
                            sec_color = theme["sunday"] if c == 6 else (theme["saturday"] if c == 5 else theme["text"])
                            
                        prim_font = font_medium
                        sec_font = font_medium
                        prim_y = by + 2
                        sec_y = by + 37
                        
                        ptex, ptw, pth = render_text(prim_str, prim_font, prim_color)
                        if ptex:
                            sdl2.SDL_RenderCopy(renderer.sdlrenderer, ptex, None, sdl2.SDL_Rect(bx + cell_w//2 - ptw//2, prim_y, ptw, pth))
                            sdl2.SDL_DestroyTexture(ptex)
                            
                        stex, stw, sth = render_text(sec_str, sec_font, sec_color)
                        if stex:
                            sdl2.SDL_RenderCopy(renderer.sdlrenderer, stex, None, sdl2.SDL_Rect(bx + cell_w//2 - stw//2, sec_y, stw, sth))
                            sdl2.SDL_DestroyTexture(stex)

            # Footer
            mode_str = "[Solar]" if view_mode == MODE_SOLAR else "[Lunar]"
            footer = f"L/R: Month | L2/R2: Year | DPAD: Move | X: {mode_str} | Y: Theme | A: Today | START: Exit"
            tex, tw, th = render_text(footer, font_small, theme["text_dim"])
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)

            if show_quit_confirm:
                sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
                sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 0, 0, 0, 150)
                sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
                
                pop_w, pop_h = 600, 200
                pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
                
                renderer.fill((pop_x, pop_y, pop_w, pop_h), theme["sel_border"])
                renderer.fill((pop_x+2, pop_y+2, pop_w-4, pop_h-4), theme["bg"])
                
                msg = "Exit Calendar?"
                tex, tw, th = render_text(msg, font_large, theme["text"])
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 40, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                
                msg2 = "A: Confirm   B: Cancel"
                tex, tw, th = render_text(msg2, font_medium, theme["text_dim"])
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 120, tw, th))
                    sdl2.SDL_DestroyTexture(tex)

            renderer.present()
            needs_redraw = False
            
        sdl2.SDL_Delay(16)

    sdlttf.TTF_CloseFont(font_large)
    sdlttf.TTF_CloseFont(font_medium)
    sdlttf.TTF_CloseFont(font_small)
    sdlttf.TTF_Quit()
    sdl2.SDL_Quit()

if __name__ == "__main__":
    main()
