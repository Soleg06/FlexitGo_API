import flexitGo_API
from pprint import pprint

fg = flexitGo_API.FlexitGo()
fg.login("firstname.lastname@something.com","*********")

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

