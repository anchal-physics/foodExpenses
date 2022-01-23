import gspread
import numpy as np
from datetime import datetime, date
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

monthlyAllowance = 500


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
    # remAllowance = monthlyAllowance
    tt = [date(today.year, today.month, day) for day in range(1, totalDays+1)]
    dailyCosts = np.zeros(len(tt))
    perDiumCost = np.zeros_like(dailyCosts)
    todayInd = today.day - 1
    for ii in range(noEntries):
        if today.month == dates[ii].month:
            ttind = dates[ii].day - 1
            dF = int(daysFor[ii])
            dailyCosts[ttind] += cost[ii]
            perDiumCost[ttind:ttind+dF] += np.ones(dF) * cost[ii] / dF
    todayAllowance = ((monthlyAllowance - np.sum(perDiumCost[:todayInd]))
                      / (totalDays - todayInd))
    thisWeekAllow = todayAllowance * (7 - today.weekday())
    todayRemAllow = todayAllowance - perDiumCost[todayInd]
    thisWeekRemAllow = (thisWeekAllow
                        - perDiumCost[todayInd:todayInd + 7 - today.weekday()])

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

    fig, ax = plt.subplots(1, 1, figsize=[16, 12])
    ax.bar(tt, perDiumCost, label='Effective daily expense',
           color='tab:olive')
    ax.bar(tt, dailyCosts, label='Daily Costs', color='tab:orange', alpha=0.3)
    ax.plot(tt, monthlyAllowance - np.cumsum(dailyCosts),
            label='Remaining Allowance', color='green')
    ax.plot(ttSA, showedAllowance, label='Showed allowance',
            color='tab:blue', ls='--')
    ax.legend()
    ax.set_title('Daily food expenses and remaining allowance')
    ax.set_ylabel('Cost [$]')
    ax.text(tt[3], monthlyAllowance/2,
            '{}\nAllowance today (Total/Rem.): \${} / \${}\n'
            'Allowance this week (Total/Rem.): \${} / \${}'.format(
                today.strftime('%b %d, %Y'), todayAllowance, todayRemAllow,
                thisWeekAllow, thisWeekRemAllow),
            fontsize=36, color='red')
    fig.autofmt_xdate()
    fig.savefig('DailyCostsAndParameters.png')


if __name__ == "__main__":
    foodExpenses()
