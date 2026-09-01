#!/usr/bin/env python3
import os
import sys
import datetime
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

# Colors (Warm Paper Vintage Calendar)
BG_COLOR = sdl2.ext.Color(245, 241, 230)           # #F5F1E6
TEXT_COLOR = sdl2.SDL_Color(51, 48, 43, 255)       # #33302B
TEXT_DIM = sdl2.SDL_Color(111, 106, 96, 255)       # #6F6A60
SEL_COLOR = sdl2.ext.Color(102, 137, 181)          # #6689B5
SEL_BG_COLOR = sdl2.ext.Color(229, 235, 241)       # #E5EBF1
HEADER_COLOR = sdl2.SDL_Color(48, 46, 42, 255)     # #302E2A
SUNDAY_COLOR = sdl2.SDL_Color(182, 92, 92, 255)    # #B65C5C
SATURDAY_COLOR = sdl2.SDL_Color(88, 112, 128, 255) # #587080
LUNAR_COLOR = sdl2.SDL_Color(107, 91, 149, 255)    # #6B5B95
TODAY_BORDER = sdl2.ext.Color(217, 184, 108)       # #D9B86C

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
    for i in range(num_joysticks):
        if sdl2.SDL_IsGameController(i):
            sdl2.SDL_GameControllerOpen(i)

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
    
    l2_pressed = False
    r2_pressed = False
    
    view_mode = MODE_SOLAR

    weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    month_names = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    
    running = True
    show_quit_confirm = False
    while running:
        needs_redraw = True
        events = sdl2.ext.get_events()
        if len(events) > 0:
            needs_redraw = True
            
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_ESCAPE:
                    running = False
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
                    cursor_day = max(1, cursor_day - 7)
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                    cursor_day = min(get_days_in_month(cur_year, cur_month), cursor_day + 7)
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                    cursor_day = max(1, cursor_day - 1)
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                    cursor_day = min(get_days_in_month(cur_year, cur_month), cursor_day + 1)
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_B:
                    now_t = datetime.datetime.now()
                    cur_year = now_t.year
                    cur_month = now_t.month
                    cursor_day = now_t.day
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_X: # Physical Y on TrimUI
                    view_mode = MODE_LUNAR if view_mode == MODE_SOLAR else MODE_SOLAR
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
            renderer.clear(BG_COLOR)
            w_w, w_h = 1024, 768
            
            # Draw Header
            if view_mode == MODE_SOLAR:
                header = f"SOLAR {cursor_day:02d}-{cur_month:02d}-{cur_year:04d}"
                header_color = TEXT_COLOR
                sdlttf.TTF_SetFontStyle(font_large, sdlttf.TTF_STYLE_BOLD)
            else:
                try:
                    ld, lm, ly, _ = convertSolar2Lunar(cursor_day, cur_month, cur_year)
                    header = f"LUNAR {ld:02d}-{lm:02d}-{ly:04d}"
                except Exception:
                    header = f"LUNAR {cursor_day:02d}-{cur_month:02d}-{cur_year:04d}"
                header_color = LUNAR_COLOR
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
                color = SUNDAY_COLOR if i == 6 else (SATURDAY_COLOR if i == 5 else HEADER_COLOR)
                tex, tw, th = render_text(wd, font_medium, color)
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(start_x + i * cell_w + cell_w//2 - tw//2, start_y + 10, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                    
            # Draw Days
            start_y += 70
            cal = get_month_calendar(cur_year, cur_month)
            
            # Draw Grid
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 221, 215, 200, 255) # Faint grid color #DDD7C8
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
                            draw_border(renderer, rx, ry, rw, rh, TODAY_BORDER, BG_COLOR, thickness=3)
                            
                        is_cursor = (day == cursor_day)
                        if is_cursor:
                            # Draw selected border around cursor
                            rx, ry = bx + 1, by - 4
                            rw, rh = cell_w - 2, cell_h - 2
                            draw_border(renderer, rx, ry, rw, rh, SEL_COLOR, SEL_BG_COLOR, thickness=2)
                        
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
                            prim_color = SUNDAY_COLOR if c == 6 else (SATURDAY_COLOR if c == 5 else TEXT_COLOR)
                            sec_color = LUNAR_COLOR
                        else:
                            prim_str = lunar_str
                            sec_str = str(day)
                            prim_color = LUNAR_COLOR
                            sec_color = SUNDAY_COLOR if c == 6 else (SATURDAY_COLOR if c == 5 else TEXT_COLOR)
                            
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
            footer = f"L/R: Month | L2/R2: Year | D-Pad: Move | Y: {mode_str} | A: Today | START: Exit"
            tex, tw, th = render_text(footer, font_small, TEXT_DIM)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)

            if show_quit_confirm:
                sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
                sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, 0, 0, 0, 150)
                sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
                
                pop_w, pop_h = 600, 200
                pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
                
                renderer.fill((pop_x, pop_y, pop_w, pop_h), TEXT_COLOR)
                renderer.fill((pop_x+2, pop_y+2, pop_w-4, pop_h-4), BG_COLOR)
                
                msg = "Exit Calendar?"
                tex, tw, th = render_text(msg, font_large, TEXT_COLOR)
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 40, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                
                msg2 = "A: Confirm   B: Cancel"
                tex, tw, th = render_text(msg2, font_medium, TEXT_DIM)
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
