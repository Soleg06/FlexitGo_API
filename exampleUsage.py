import olis_flexitgo
from pprint import pprint

fg = olis_flexitgo.FlexitGo()
fg.login("firsname.lastname@something.com","*********")

pprint(fg.getSensors())
pprint(fg.getDevice())

#pprint(fg.setAwayTemp(18))
#pprint(fg.setHomeTemp(22))

#pprint(fg.setPresetMode("AWAY"))
#pprint(fg.setPresetMode("AWAY_DELAYED"))
#pprint(fg.setPresetMode("HOME"))
#pprint(fg.setPresetMode("HIGH"))
#pprint(fg.setPresetMode("HIGH_ONTIMER"))
#pprint(fg.setPresetMode("FIREPLACE"))

#pprint(fg.setHeaterState(False))

#fg.setFireplaceDuration(duration)
#fg.setBoostDuration(duration)
#fg.setAwayDelay(delay):
#fg.setCalendarActive()
#fg.setCalendarTemporaryOverride(value)

