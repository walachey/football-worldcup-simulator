# coding=utf-8
import re
from bs4 import BeautifulSoup
import urllib

url = "http://www.oddschecker.com/football/world-cup/winner"

try:
	from urllib2 import urlopen, Request
	import urllib2
	from urllib import urlencode
except ImportError:
	from urllib.request import urlopen, urlencode # py3k

class Team:
	odds = None
	name = None
	
	def __init__(self):
		self.odds = []
		
	def addOdd(self, odd):
		self.odds.append(odd)
	
	def getAvg(self):
		sum = 0.0
		for odd in self.odds:
			sum += odd
		sum /= float(len(self.odds))
		return sum
		


def getResults():
	names_repl = {
	"Bosnia-Herzegovina": "Bosnia and Herzegovina",
	"South Korea": "Korea Republic"
	}

	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]

	soup = None
	try:
		request = Request(url)
		soup = BeautifulSoup(opener.open(request))
	except urllib2.HTTPError, e:
		print "EXECPTION: " + str(e)
		print "HEADER\t" + str(e.headers)
		print "CODE\t" + str(e.code)
		print "MSG\t" + str(e.msg)
		soup = BeautifulSoup(e.fp.read());
		print str(soup)
	
	table = soup.find("table", { "class" : "eventTable" })
	body = table.find("tbody")
	
	teams = []
	for row in body.find_all("tr"):
		team = Team()
		name_field = row.find("td", { "class" : "sel nm" })
		name_field = name_field.find("span", { "class" : "add-to-bet-basket" })
		team.name = name_field["data-name"]
		if team.name in names_repl:
			team.name = names_repl[team.name]
		for odd_field in row.find_all("td", attrs={'class': re.compile(r".*\bbgc\b.*")}):
			odd = odd_field.renderContents().strip()
			if odd.find("/") != -1:
				s = odd.split("/")
				odd = float(s[0]) / float(s[1])
			else:
				odd = float(odd)
			# print "\t" + str(odd) + "\t <- " + odd_field.renderContents().strip() 
			team.addOdd(odd)
		teams.append(team)
	return teams
if __name__ == "__main__":
	teams = getResults()
	
	for team in teams:
		print team.name + "\t" + str(1.0 / (1.0 + team.getAvg())) + "\t" + str(team.getAvg()) + "\n"