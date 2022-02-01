import gspread
import numpy as np
from traceback import print_exc
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt  # For plotting
# *****************************************************************************
# Setting RC Parameters for figure size and fontsizes
import matplotlib.pylab as pylab
params = {'figure.figsize': (16, 12),
          'xtick.labelsize': 'medium',
          'ytick.labelsize': 'medium',
          'text.usetex': False,
          'lines.linewidth': 4,
          'font.family': 'serif',
          'font.serif': 'Georgia',
          'font.size': 20,
          'xtick.direction': 'in',
          'ytick.direction': 'in',
          'axes.labelsize': 'x-large',
          'axes.titlesize': 'x-large',
          'axes.grid.axis': 'both',
          'axes.grid.which': 'both',
          'axes.grid': True,
          'grid.color': 'xkcd:cement',
          'grid.alpha': 0.3,
          'lines.markersize': 6,
          'legend.borderpad': 0.2,
          'legend.fancybox': True,
          'legend.fontsize': 'medium',
          'legend.framealpha': 0.8,
          'legend.handletextpad': 0.5,
          'legend.labelspacing': 0.33,
          'legend.loc': 'best',
          'savefig.dpi': 140,
          'savefig.bbox': 'tight',
          'pdf.compression': 9}
pylab.rcParams.update(params)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name(
                                            'foodexpenses-663287ec7fd3.json',
                                            scope)

defaultMonthlyAllowance = 500
startDate = date(2022, 1, 1)


def parse(data, ii, ind):
    if data[ii][ind] == '':
        return np.NaN
    else:
        return float(data[ii][ind])


def parseDate(data, ii, ind):
    if data[ii][ind] == '':
        return datetime.strptime(data[ii][0], '%m/%d/%Y %H:%M:%S').date()
    else:
        return datetime.strptime(data[ii][ind], '%m/%d/%Y').date()


def getData(spName="Food/Groceries expense monitor (Responses)",
            credentials=credentials):
    gc = gspread.authorize(credentials)
    sh = gc.open(spName)
    wks = sh.get_worksheet(0)
    ts = wks.col_values(1)[1:]
    data = wks.get_all_values()[1:][:]
    return ts, data


def getMonthlyAllowance(dat):
    with open('monthlyAllowance.txt', 'r') as f:
        allLines = f.readlines()
        monArr = []
        monAll = []
        for line in allLines:
            splits = line.split(' ')
            monArr += [datetime.strptime(splits[0], '%m/%d/%Y').date()]
            monAll += [int(splits[1])]
    for ii, mon in enumerate(monArr):
        if dat.year == mon.year and dat.month == mon.month:
            return monAll[ii]
    with open('monthlyAllowance.txt', 'a+') as f:
        f.write(dat.strftime('%m/%d/%Y ')
                + str(defaultMonthlyAllowance) + '\n')
        return defaultMonthlyAllowance


def allAllowances():
    dat = startDate
    allowance = 0
    while dat <= datetime.now().date():
        allowance += getMonthlyAllowance(dat)
        dat = dat + relativedelta(months=1)
    return allowance


def foodExpenses():
    ts, data = getData()
    noEntries = len(ts)
    cost = np.zeros(noEntries)
    daysFor = np.zeros(noEntries)
    dates = [None] * noEntries
    for ii in range(noEntries):
        cost[ii] = parse(data, ii, 1)
        daysFor[ii] = parse(data, ii, 2)
        dates[ii] = parseDate(data, ii, 3)

    today = datetime.now().date()
    totalDays = monthrange(today.year, today.month)[1]
    ttlen = date(today.year, today.month + 2, 1) - startDate
    tt = [startDate + timedelta(days=int(ii)) for ii in range(ttlen.days)]
    dailyCosts = np.zeros(ttlen.days)
    perDiumCost = np.zeros_like(dailyCosts)
    remAllow = np.zeros_like(dailyCosts)
    monLen = ((today.year - startDate.year) * 12
              + today.month - startDate.month + 1)
    monArr = [startDate + relativedelta(months=ii)
              for ii in range(monLen)]
    monArr2 = [dat + relativedelta(days=monthrange(dat.year, dat.month)[1]//2)
               for dat in monArr]
    monArr2[-1] = monArr[-1] + relativedelta(days=(today - monArr[-1]).days//2)
    monWidths = [monthrange(ele.year, ele.month)[1] * 0.95 for ele in monArr]
    monWidths[-1] = (today - monArr[-1]).days * 0.95
    monCosts = np.zeros(monLen)
    todayInd = tt.index(today)
    monEndInd = tt.index(date(today.year, today.month, 1)
                         + relativedelta(months=1))
    weekEndInd = min(todayInd + 7 - today.weekday(), monEndInd)

    for ii in range(noEntries):
        ttind = tt.index(dates[ii])
        monInd = monArr.index(date(dates[ii].year, dates[ii].month, 1))
        dF = int(daysFor[ii])
        dailyCosts[ttind] += cost[ii]
        perDiumCost[ttind:ttind+dF] += np.ones(dF) * cost[ii] / dF
        monCosts[monInd] += cost[ii]

    for ii in range(ttlen.days):
        if ii != 0:
            remAllow[ii] = remAllow[ii-1]
        if tt[ii].day == 1:
            remAllow[ii] += getMonthlyAllowance(tt[ii])
        remAllow[ii] -= dailyCosts[ii]


    thisMonRemAllow = allAllowances() - np.sum(perDiumCost[:todayInd])
    todayAllowance = thisMonRemAllow / (totalDays - today.day + 1)
    thisWeekAllow = todayAllowance * (7 - today.weekday())
    todayRemAllow = todayAllowance - perDiumCost[todayInd]
    thisWeekRemAllow = (thisWeekAllow
                        - np.sum(perDiumCost[todayInd:weekEndInd]))

    with open('showedAllowance.txt', 'r') as f:
        allLines = f.readlines()
    showedAllowance = np.zeros(len(allLines))
    ttSA = [None] * len(allLines)
    for ii in range(len(allLines)):
        ttSA[ii] = datetime.strptime(allLines[ii].split(' ')[0],
                                     '%Y/%m/%d').date()
        showedAllowance[ii] = float(allLines[ii].split(' ')[1])

    todayAllowance = int(todayAllowance)
    todayRemAllow = int(todayRemAllow)
    thisWeekAllow = int(thisWeekAllow)
    thisWeekRemAllow = int(thisWeekRemAllow)
    thisMonRemAllow = int(thisMonRemAllow)

    writeOver = False
    if ttSA[-1] != today:
        ttSA.append(today)
        showedAllowance = np.append(showedAllowance, todayAllowance)
        writeOver = True
    elif showedAllowance[-1] != todayAllowance:
        showedAllowance[-1] = todayAllowance
        writeOver = True
    if writeOver:
        with open('showedAllowance.txt', 'w') as f:
            for ii in range(len(ttSA)):
                f.writelines(ttSA[ii].strftime('%Y/%m/%d ')
                             + str(showedAllowance[ii]) + '\n')

    i0 = tt.index(date(today.year, today.month, 1))
    i1 = tt.index(date(today.year, today.month + 1, 1))
    for ii in range(1, totalDays + 1):
        try:
            i2 = ttSA.index(date(today.year, today.month, ii))
            break
        except BaseException:
            pass

    motd = '{}\nAllowance today (Total/Rem.): \${} / \${}\n'.format(
                    today.strftime('%b %d, %Y'), todayAllowance, todayRemAllow)
    if monEndInd - todayInd > 7:
        motd += 'Allowance this week (Total/Rem.): \${} / \${}'.format(
                    thisWeekAllow, thisWeekRemAllow)
    else:
        motd += 'Remaining allowance this month : \${}'.format(thisMonRemAllow)

    fig, ax = plt.subplots(1, 1, figsize=[16, 12])
    ax.bar(tt[i0:i1], perDiumCost[i0:i1], label='Effective daily expense',
           color='tab:olive')
    ax.bar(tt[i0:i1], dailyCosts[i0:i1], label='Daily Costs',
           color='tab:orange', alpha=0.3)
    ax.plot(tt[i0:i1],remAllow[i0:i1], label='Remaining Allowance',
            color='green')
    # ax.plot(tt[i0:i1], (monthlyAllowance - np.cumsum(dailyCosts))[i0:i1],
    #         label='Remaining Allowance', color='green')
    ax.plot(ttSA[i2:], showedAllowance[i2:], label='Showed allowance',
            color='tab:blue', ls='--')
    ax.legend()
    ax.set_title('Daily food expenses and remaining allowance')
    ax.set_ylabel('Cost [$]')
    ax.text(tt[i0 + 3], 250, motd, fontsize=36, color='red')
    fig.autofmt_xdate()
    fig.savefig('DailyCostsAndParameters.png')


    fig, ax = plt.subplots(1, 1, figsize=[16, 12])
    ax.bar(monArr2, monCosts, label='Monthly Costs', color='grey',
           width=monWidths, alpha=0.3)
    ax.bar(tt[:todayInd + 1], perDiumCost[:todayInd + 1], label='Effective daily expense',
           color='tab:olive')
    ax.bar(tt[:todayInd + 1], dailyCosts[:todayInd + 1], label='Daily Costs',
           color='tab:orange', alpha=0.3)
    ax.plot(tt[:todayInd + 1],remAllow[:todayInd + 1], label='Remaining Allowance',
            color='green')
    # ax.plot(tt[i0:i1], (monthlyAllowance - np.cumsum(dailyCosts))[i0:i1],
    #         label='Remaining Allowance', color='green')
    ax.plot(ttSA, showedAllowance, label='Showed allowance',
            color='tab:blue', ls='--')
    ax.legend()
    ax.set_title('Daily food expenses and remaining allowance')
    ax.set_ylabel('Cost [$]')
    fig.autofmt_xdate()
    fig.savefig('allTimeCostsAndParameters.png')


if __name__ == "__main__":
    foodExpenses()
