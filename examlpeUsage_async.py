#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from pprint import pprint

from codetiming import Timer

from flexitGo_API_async import *
                
            
async def main():
    fg = FlexitGo() 
    await fg.login("firstname.lastname@something.com","*********")
    #pprint(fg.getPlant())
    #await fg._validateToken()

    pprint(await fg.getSensors())

    pprint(await fg.getDevice())
    #pprint(await fg.setAwayTemp(18))
    #pprint(await fg.setHomeTemp(22))

    #pprint(await fg.setPresetMode("AWAY"))
    #pprint(await fg.setPresetMode("AWAY_DELAYED"))
    #pprint(await fg.setPresetMode("HOME"))
    #pprint(await fg.setPresetMode("HIGH"))
    #pprint(await fg.setPresetMode("HIGH_ONTIMER"))
    #pprint(await fg.setPresetMode("FIREPLACE"))

    #pprint(await fg.setHeaterState(False))

    #await fg.setFireplaceDuration(duration)
    #await fg.setBoostDuration(duration)
    #await fg.setAwayDelay(delay):
    #await fg.setCalendarActive()
    #await fg.setCalendarTemporaryOverride(value)

asyncio.run(main())