import math

# Lunar calendar calculation logic based on Ho Ngoc Duc's algorithm
# Adapted for Python

def jdFromDate(dd, mm, yyyy):
    a = (14 - mm) // 12
    y = yyyy + 4800 - a
    m = mm + 12*a - 3
    jd = dd + ((153*m + 2)//5) + 365*y + y//4 - y//100 + y//400 - 32045
    if jd < 2299161:
        jd = dd + ((153*m + 2)//5) + 365*y + y//4 - 32083
    return jd

def jdToDate(jd):
    if jd > 2299160:
        a = jd + 32044
        b = (4*a + 3) // 146097
        c = a - (146097*b)//4
        d = (4*c + 3) // 1461
        e = c - (1461*d)//4
        m = (5*e + 2) // 153
        day = e - (153*m + 2)//5 + 1
        month = m + 3 - 12*(m//10)
        year = b*100 + d - 4800 + m//10
    else:
        b = jd + 32082
        c = (4*b + 3) // 1461
        d = b - (1461*c)//4
        e = (5*d + 2) // 153
        day = d - (153*e + 2)//5 + 1
        month = e + 3 - 12*(e//10)
        year = c - 4800 + e//10
    return day, month, year

def getSunLongitude(dayNumber, timeZone):
    D = dayNumber - 2451545.0
    g = 357.529 + 0.98560028 * D
    q = 280.459 + 0.98564736 * D
    L = q + 1.915 * math.sin(g * math.pi / 180) + 0.020 * math.sin(2 * g * math.pi / 180)
    L = L % 360
    return L

def getNewMoonDay(k, timeZone):
    T = k / 1236.85
    T2 = T * T
    T3 = T2 * T
    dr = math.pi / 180
    Jd = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
    Jd = Jd + 0.00033 * math.sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
    M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
    Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
    F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
    C = (0.1734 - 0.000393 * T) * math.sin(M * dr) + 0.0021 * math.sin(2 * M * dr)
    C = C - 0.0004 * math.sin(Mpr * dr) + 0.0005 * math.sin(2 * F * dr)
    E = 0.0004 * math.sin((313.45 + 481267.884 * T - 0.00111 * T2) * dr)
    newMoon = Jd + C + E + 0.5 + timeZone / 24
    return math.floor(newMoon)

def getLunarMonth11(yyyy, timeZone):
    off = jdFromDate(31, 12, yyyy) - 2415021
    k = math.floor(off / 29.530588853)
    nm = getNewMoonDay(k, timeZone)
    sunLong = getSunLongitude(nm, timeZone)
    if sunLong >= 285: nm = getNewMoonDay(k - 1, timeZone)
    return nm

def getLeapMonthOffset(a11, timeZone):
    k = math.floor((a11 - 2415021) / 29.530588853) + 0.5
    last = 0
    i = 1
    arc = getSunLongitude(getNewMoonDay(k, timeZone), timeZone)
    while True:
        last = arc
        i += 1
        arc = getSunLongitude(getNewMoonDay(k + i, timeZone), timeZone)
        if i == 14: return 0
        if math.floor(arc / 30) == math.floor(last / 30):
            return i

def convertSolar2Lunar(dd, mm, yyyy, timeZone=7.0):
    dayNumber = jdFromDate(dd, mm, yyyy)
    k = math.floor((dayNumber - 2415021) / 29.530588853)
    monthStart = getNewMoonDay(k + 1, timeZone)
    if monthStart > dayNumber:
        monthStart = getNewMoonDay(k, timeZone)
    else:
        k = k + 1
    
    a11 = getLunarMonth11(yyyy, timeZone)
    b11 = a11
    if a11 >= monthStart:
        a11 = getLunarMonth11(yyyy - 1, timeZone)
    else:
        b11 = getLunarMonth11(yyyy + 1, timeZone)
        
    day = dayNumber - monthStart + 1
    diff = int((monthStart - a11) / 29)
    leapMonthDiff = getLeapMonthOffset(a11, timeZone)
    
    isLeap = 0
    leapMonth = 0
    if b11 - a11 > 365:
        leapMonth = leapMonthDiff
    
    month = diff - 1
    if diff == 0: month = 11
    if diff == 1: month = 12
    if month > 12: month -= 12
    
    if leapMonth != 0 and diff >= leapMonth:
        month = month - 1
        if month == 0: month = 12
        if month > 12: month -= 12
        if diff == leapMonth: isLeap = 1
        
    year = yyyy
    if month == 11 or month == 12: year = yyyy
    else:
        if monthStart < b11 - 365: year = yyyy - 1
        
    return day, month, year, isLeap
