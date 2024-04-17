#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import urllib.parse

import aiohttp
import arrow
import structlog
import ujson


class FlexitGo:

    # Put paths
    MODE_AWAY_PUT_PATH = ";1!005000032000055"
    MODE_HOME_HIGH_CAL_PUT_PATH = ";1!01300002A000055"
    MODE_HIGH_TEMP_PUT_PATH = ";1!013000165000055"  # TOGGLES
    MODE_FIREPLACE_PUT_PATH = ";1!013000168000055"  # TOGGLES

    FIREPLACE_DURATION_PATH = ";1!03000010E000055"  # PUT AND GET
    BOOST_DURATION_PATH = ";1!030000125000055"  # PUT AND GET
    AWAY_DELAY_PATH = ";1!03000013E000055"  # PUT AND GET
    CALENDAR_TEMPORARY_OVERRIDE_PATH = ";1!0050001DA000055"  # PUT AND GET

    # Paths
    HOME_AIR_TEMPERATURE_PATH = ";1!0020007CA000055"
    AWAY_AIR_TEMPERATURE_PATH = ";1!0020007C1000055"
    ROOM_TEMPERATURE_PATH = ";1!00000004B000055"
    CURRENT_FIREPLACE_DURATION_PATH = ";1!0020007F6000055"
    CURRENT_BOOST_DURATION_PATH = ";1!0020007EF000055"

    # Null*Off*Away*Home*High*Cocker hood*Fire place*Forced ventilation
    MODE_PATH = ";1!013000169000055"  # Null*Off*Away*Home*High*Cocker hood*Fire place*Forced ventilation
    OUTSIDE_AIR_TEMPERATURE_PATH = ";1!000000001000055"  # Uteluft
    SUPPLY_AIR_TEMPERATURE_PATH = ";1!000000004000055"  # Tilluft
    EXTRACT_AIR_TEMPERATURE_PATH = ";1!00000003B000055"  # Avtrekk
    EXHAUST_AIR_TEMPERATURE_PATH = ";1!00000000B000055"  # Avkast
    HEATER_PATH = ";1!0050001BD000055"
    FILTER_OPERATING_TIME_PATH = ";1!00200011D000055"
    FILTER_TIME_FOR_EXCHANGE_PATH = ";1!00200011E000055"
    ALARM_CODE_A_PATH = ";1!002000008000055"
    ALARM_CODE_B_PATH = ";1!002000082000055"

    HEAT_EXCHANGER_SPEED_PATH = ";1!001000000000055"
    SUPPLY_FAN_SPEED_PATH = ";1!000000005000055"
    SUPPLY_FAN_CONTROL_SIGNAL_PATH = ";1!001000003000055"
    EXTRACT_FAN_SPEED_PATH = ";1!00000000C000055"
    EXTRACT_FAN_CONTROL_SIGNAL_PATH = ";1!001000004000055"
    ADDITIONAL_HEATER_PATH = ";1!00100001D000055"

    OFFLINE_ONLINE_PATH = ";0!Online"
    LAST_RESTART_REASON_PATH = ";0!0083FFFFF0000C4"
    SYSTEM_STATUS_PATH = ";0!0083FFFFF000070"

    APPLICATION_SOFTWARE_VERSION_PATH = ";0!0083FFFFF00000C"
    DEVICE_DESCRIPTION_PATH = ";0!0083FFFFF00001C"
    MODEL_NAME_PATH = ";0!0083FFFFF000046"
    MODEL_INFORMATION_PATH = ";0!0083FFFFF0012DB"
    SERIAL_NUMBER_PATH = ";0!0083FFFFF0013EC"
    FIRMWARE_REVISION_PATH = ";0!0083FFFFF00002C"
    BACNET_MAC_PATH = ";0!108000000001313"
    DEVICE_FEATURES_PATH = ";0!0083FFFFF0013F4"

    SENSOR_DATA_PATH_LIST = [MODE_PATH,
                             MODE_HOME_HIGH_CAL_PUT_PATH,
                             OUTSIDE_AIR_TEMPERATURE_PATH,
                             SUPPLY_AIR_TEMPERATURE_PATH,
                             EXTRACT_AIR_TEMPERATURE_PATH,
                             EXHAUST_AIR_TEMPERATURE_PATH,
                             HOME_AIR_TEMPERATURE_PATH,
                             AWAY_AIR_TEMPERATURE_PATH,
                             ROOM_TEMPERATURE_PATH,
                             FILTER_OPERATING_TIME_PATH,
                             FILTER_TIME_FOR_EXCHANGE_PATH,
                             HEATER_PATH,
                             HEAT_EXCHANGER_SPEED_PATH,
                             SUPPLY_FAN_SPEED_PATH,
                             SUPPLY_FAN_CONTROL_SIGNAL_PATH,
                             EXTRACT_FAN_SPEED_PATH,
                             EXTRACT_FAN_CONTROL_SIGNAL_PATH,
                             ADDITIONAL_HEATER_PATH,
                             ALARM_CODE_A_PATH,
                             ALARM_CODE_B_PATH,
                             BOOST_DURATION_PATH,
                             FIREPLACE_DURATION_PATH,
                             AWAY_DELAY_PATH,
                             CALENDAR_TEMPORARY_OVERRIDE_PATH]

    DEVICE_INFO_PATH_LIST = [APPLICATION_SOFTWARE_VERSION_PATH,
                             DEVICE_DESCRIPTION_PATH,
                             MODEL_NAME_PATH,
                             MODEL_INFORMATION_PATH,
                             SERIAL_NUMBER_PATH,
                             FIRMWARE_REVISION_PATH,
                             OFFLINE_ONLINE_PATH,
                             SYSTEM_STATUS_PATH,
                             LAST_RESTART_REASON_PATH]

    API_URL = "https://api.climatixic.com"
    TOKEN_PATH = "/Token"
    PLANTS_PATH = "/Plants"
    DATAPOINTS_PATH = "/DataPoints"
    # FILTER_PATH = f"{DATAPOINTS_PATH}/Values?filterId="
    VALUES_PATH = f"{DATAPOINTS_PATH}/Values"

    log = structlog.get_logger(__name__)
    doSessionSemaphore = asyncio.Lock()
    fileReadLock = asyncio.Lock()
    fileWriteLock = asyncio.Lock()
    RETRIES = 3
    RETRY_DELAY = 10  # seconds
    tokenValidTo = None
    tokenFileName = "/home/staffan/olis/olis_flexit/tokenfile.txt"
    tokenFileRead = False
    session = aiohttp.ClientSession(base_url=API_URL)
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-us",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Flexit%20GO/2.0.6 CFNetwork/1128.0.1 Darwin/19.6.0",
        "Ocp-Apim-Subscription-Key": "c3fc1f14ce8747588212eda5ae3b439e",
        "Host": "api.climatixic.com",
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password

    @classmethod
    async def _readFileAsync(cls, filename):
        async with cls.fileReadLock:
            if os.path.exists(filename):
                with open(filename, mode="r") as file:
                    contents = ujson.load(file)
                    return contents

    @classmethod
    async def _writeFileAsync(cls, filename, contents):
        async with cls.fileWriteLock:
            with open(filename, mode="w") as file:
                ujson.dump(contents, file)

    async def _doRequest(self, method, url, headers, data=None, params=None):
        out = {}
        for i in range(self.RETRIES):
            try:
                async with FlexitGo.doSessionSemaphore:
                    async with self.session.request(method=method, url=url, headers=headers, data=data, params=params) as response:
                        out = await response.json()

                return out

            except Exception as e:
                self.log.error("Exception in _doRequest", error=e)
                if i < self.RETRIES - 1:
                    self.log.warning(f"Retrying in {self.RETRY_DELAY} seconds...")
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    self.log.warning("Max retries reached. Attempting logon...")
                    await self.login()
                    i = -1

    def _path(self, path):
        return f"{self.plantId}{path}"

    def _escaped_filter_url(self, path):
        return f"{self.FILTER_PATH}{urllib.parse.quote(path)}"

    # async def _create_url_from_paths(self, paths):
    #    url = "["
    #    for path in paths:
    #        url += f"""{{"DataPoints":"{self._path(path)}"}}{ "," if path != paths[-1] else "]"}"""
    #    return url

    def _create_url_from_paths2(self, paths):
        url = list()
        for path in paths:
            sub = {"DataPoints": self._path(path)}
            url.append(sub)
        return url

    def _escaped_datapoints_url(self, path):
        return f"{self.DATAPOINTS_PATH}/{urllib.parse.quote(path)}"

    def _str_device(self, path):
        return self.deviceData["values"][f"{self.plantId}{path}"]['value']

    def _str_sensor(self, path):
        return self.sensorData["values"][f"{self.plantId}{path}"]['value']['value']

    def _present_priority(self, path):
        return self.sensorData["values"][f"{self.plantId}{path}"]['value']["presentPriority"]

    def _int_device(self, path):
        return int(self._str_device(path))

    def _int_sensor(self, path):
        return int(self._str_sensor(path))

    def _bool_sensor(self, path):
        return bool(self._str_sensor(path))

    def _float_sensor(self, path):
        return round(float(self._str_sensor(path)), 1)

    def _calendar_active(self, path):
        if self._present_priority(path) == 15:
            return True
        else:
            return False

    def _dirty_filter(self, filter_time_for_exchange):
        if arrow.get(filter_time_for_exchange) >= arrow.now():
            return False
        else:
            return True

    def _ventilation_mode(self, ventilation_int):
        mode = {0: "Null",
                1: "OFF",
                2: "AWAY",
                3: "HOME",
                4: "HIGH",
                5: "COOKER_HOOD",
                6: "FIREPLACE",
                7: "HIGH_DELAYED"
                }
        return mode.get(ventilation_int, f"Unknown mode: {str(ventilation_int)}")

    def _to_efficiency(self, tilluft, uteluft, frånluft):
        return round(((tilluft - uteluft) / (frånluft - uteluft)) * 100, 1)

    def _from_efficiency(self, uteluft, frånluft, avluft):
        return round(((frånluft - avluft) / (frånluft - uteluft)) * 100, 1)

    async def login(self):
        for i in range(self.RETRIES):
            try:
                if not self.tokenFileRead:
                    _tokenFromFile = await self._readFileAsync(self.tokenFileName)

                if not self.tokenFileRead and _tokenFromFile:
                    if "token" in _tokenFromFile:
                        self.log.info("FlexitGo setting token from file")
                        _token = _tokenFromFile.get("token")
                        self.headers["Authorization"] = _token
                        self.tokenValidTo = arrow.get(_tokenFromFile.get("tokenExpires"), tzinfo=("Europe/Stockholm"))
                        self.tokenFileRead = True
                        await self._validateToken()
                    else:
                        self.tokenFileRead = True
                        self.log.warning("Melcloud token file damaged")
                else:
                    self.log.info("FlexitGo trying login")
                    data = f"grant_type=password&username={self.username}&password={self.password}".encode("ASCII")
                    out = await self._doRequest(method="POST", url=self.TOKEN_PATH, headers=self.headers, data=data)
                    if out is not None and 'access_token' in out:
                        _token = f"Bearer {out['access_token']}"
                        self.headers["Authorization"] = _token
                        fmt = "ddd, DD MMM YYYY HH:mm:ss ZZZ"
                        self.tokenValidTo = arrow.get(out[".expires"], fmt).to("Europe/Stockholm")
                        await self._writeFileAsync(self.tokenFileName, {"token": _token, "tokenExpires": self.tokenValidTo.format("YYYY-MM-DD HH:mm:ss")})
                        if _token:
                            self.log.info("FlexitGo login success")

                await self.getPlant()
                break

            except Exception as e:
                self.log.error("Flexitgo exception in login",  error=e)
                if i < self.RETRIES - 1:
                    self.log.info(f"Flexitgo retrying login in {self.RETRY_DELAY} seconds...")
                    await asyncio.sleep(self.RETRY_DELAY)

    async def _validateToken(self):
        now = arrow.now("Europe/Stockholm")
        if now >= self.tokenValidTo:
            self.log.info("Melcloud token expired, logging in again")
            await self.login()

    async def getPlant(self):
        out = {}
        try:
            out = await self._doRequest(method="GET", url=self.PLANTS_PATH, headers=self.headers)
            # async with self.session.get("https://api.climatixic.com/Plants", headers=self.headers) as response:
            #    out = await response.json()
            for d in out["items"]:
                self.plantId = d["id"]

        except Exception as e:
            self.log.error("Exception in getPlant",  error=e, out=out)

        return out

    async def getDevice(self):
        # url = self._escaped_filter_url(self._create_url_from_paths(self.DEVICE_INFO_PATH_LIST))
        paramlist = await self._create_url_from_paths2(self.DEVICE_INFO_PATH_LIST)
        param = {"filterId": ujson.dumps(paramlist, separators=(",", ":"))}

        try:
            self.deviceData = await self._doRequest(method="GET", url=self.VALUES_PATH, headers=self.headers, params=param)
            # async with self.session.get(self.VALUES_PATH, headers=self.headers, params=param) as response:
            #    self.deviceData = await response.json()

            # pprint(self.deviceData)

            out = {"fw": self._str_device(self.FIRMWARE_REVISION_PATH),
                   "modelName": self._str_device(self.MODEL_NAME_PATH),
                   "modelInfo": self._str_device(self.MODEL_INFORMATION_PATH),
                   "serialInfo": self._str_device(self.SERIAL_NUMBER_PATH),
                   "systemStatus": self._str_device(self.SYSTEM_STATUS_PATH),
                   "status": self._str_device(self.OFFLINE_ONLINE_PATH),
                   "deviceDescription": self._str_device(self.DEVICE_DESCRIPTION_PATH),
                   "applicationSoftwareVersion": self._str_device(self.APPLICATION_SOFTWARE_VERSION_PATH),
                   "lastRestartReason": self._int_device(self.LAST_RESTART_REASON_PATH)}

        except Exception as e:
            self.log.error("Exception in getDevice",  error=e, out=out)

        return out

    async def getSensors(self):
        await self._validateToken()
        out = {}
        # url1 = self._escaped_filter_url(self._create_url_from_paths(self.SENSOR_DATA_PATH_LIST))
        paramlist = self._create_url_from_paths2(self.SENSOR_DATA_PATH_LIST)
        param = {"filterId": ujson.dumps(paramlist, separators=(",", ":"))}
        now = arrow.now("Europe/Stockholm")

        try:
            self.sensorData = await self._doRequest(method="GET", url=self.VALUES_PATH, headers=self.headers, params=param)

            out["temps"] = {"home_air_temperature": self._float_sensor(self.HOME_AIR_TEMPERATURE_PATH),
                            "away_air_temperature": self._float_sensor(self.AWAY_AIR_TEMPERATURE_PATH),
                            "Uteluft": self._float_sensor(self.OUTSIDE_AIR_TEMPERATURE_PATH),
                            "Tilluft": self._float_sensor(self.SUPPLY_AIR_TEMPERATURE_PATH),
                            "Avluft": self._float_sensor(self.EXHAUST_AIR_TEMPERATURE_PATH),
                            "Frånluft": self._float_sensor(self.EXTRACT_AIR_TEMPERATURE_PATH),
                            "room_temperature": self._float_sensor(self.ROOM_TEMPERATURE_PATH)}

            out["temps"]["verkningsgrad_tilluft"] = self._to_efficiency(out["temps"]["Tilluft"], out["temps"]["Uteluft"], out["temps"]["Frånluft"])
            out["temps"]["verkningsgrad_frånluft"] = self._from_efficiency(out["temps"]["Uteluft"], out["temps"]["Frånluft"], out["temps"]["Avluft"])

            out["modes"] = {"electric_heater": self._bool_sensor(self.HEATER_PATH),
                            "ventilation_mode": self._ventilation_mode(self._int_sensor(self.MODE_PATH)),
                            "ventilation_mode_cal": self._ventilation_mode(self._int_sensor(self.MODE_HOME_HIGH_CAL_PUT_PATH)),
                            "heat_exchanger_speed": self._int_sensor(self.HEAT_EXCHANGER_SPEED_PATH),
                            "additional_heater": self._bool_sensor(self.ADDITIONAL_HEATER_PATH),
                            "calendar_temporary_override": self._bool_sensor(self.CALENDAR_TEMPORARY_OVERRIDE_PATH),
                            "calendar_active": self._calendar_active(self.MODE_HOME_HIGH_CAL_PUT_PATH),
                            "boost_duration": self._int_sensor(self.BOOST_DURATION_PATH),
                            "away_delay": self._int_sensor(self.AWAY_DELAY_PATH),
                            "fireplace_duration": self._int_sensor(self.FIREPLACE_DURATION_PATH)}

            out["fläkt"] = {"supply_fan_speed": self._int_sensor(self.SUPPLY_FAN_SPEED_PATH),
                            "supply_fan_control_signal": self._float_sensor(self.SUPPLY_FAN_CONTROL_SIGNAL_PATH),
                            "extract_fan_speed": self._int_sensor(self.EXTRACT_FAN_SPEED_PATH),
                            "extract_fan_control_signal": self._float_sensor(self.EXTRACT_FAN_CONTROL_SIGNAL_PATH)}

            out["alarm"] = {"alarm_code_a": self._int_sensor(self.ALARM_CODE_A_PATH),
                            "alarm_code_b": self._int_sensor(self.ALARM_CODE_B_PATH)}

            out["filter"] = {"filter_exchanged": now.shift(hours=-self._int_sensor(self.FILTER_OPERATING_TIME_PATH)).format("YYYY-MM-DD"),
                             "filter_time_for_exchange": now.shift(hours=self._int_sensor(self.FILTER_TIME_FOR_EXCHANGE_PATH) - self._int_sensor(self.FILTER_OPERATING_TIME_PATH)).format("YYYY-MM-DD")}
            out["filter"]["dirty_filter"] = self._dirty_filter(out["filter"]["filter_time_for_exchange"])

            out["timestamp"] = now.format("YYYY-MM-DD HH:mm:ss")

        except Exception as e:
            self.log.error("Exception in getSensors",  error=e, out=out)

        return out

    async def setSensor(self, path, body):
        await self._validateToken()
        data_body = None if body is None else str(body)
        url = self._escaped_datapoints_url(self._path(path))
        data = ujson.dumps({"Value": data_body})

        try:
            out = await self._doRequest(method="PUT", url=url, headers=self.headers, data=data)
            # async with self.session.put(url, headers=self.headers, data=data) as response:
            #    out = await response.json()

            return out["stateTexts"][self._path(path)] == "Success"

        except Exception as e:
            self.log.error("Exception in setSensor",  error=e, out=out)
            return False

    async def setHomeTemp(self, temp):
        return await self.setSensor(self.HOME_AIR_TEMPERATURE_PATH, temp)

    async def setAwayTemp(self, temp):
        return await self.setSensor(self.AWAY_AIR_TEMPERATURE_PATH, temp)

    async def setPresetMode(self, presetMode):
        acceptedModes = ["HOME", "AWAY", "AWAY_DELAYED", "HIGH", "HIGH_ONTIMER", "FIREPLACE"]

        if presetMode not in acceptedModes:
            self.log.warning(f"{presetMode} are not a valid  mode!")
            return False

        currentMode = await self.getSensors()
        currentMode = currentMode["modes"]["ventilation_mode"]
        result = list()

        if currentMode == presetMode:
            return None

        # Toggle modes that requires toggle
        toggleChange = {"AWAY": "AWAY_DELAYED",
                        "HIGH_ONTIMER": "HIGH_ONTIMER",
                        "FIREPLACE": "FIREPLACE"}
        if currentMode in toggleChange:
            result.append(await self._setMode(toggleChange[currentMode]))
            # print(f"Flexitgo switching från {currentMode} to {toggleChange[currentMode]}")
            self.log.info(f"Flexitgo switching från {currentMode} to {toggleChange[currentMode]}")

        result.append(await self._setMode(presetMode))
        # print(f"Flexitgo switching mode to {presetMode}")
        self.log.info(f"Flexitgo switching mode to {presetMode}")

        return all(result)

    async def _setMode(self, mode):
        if mode == "AWAY":
            return await self.setSensor(self.MODE_AWAY_PUT_PATH, 0)
        elif mode == "AWAY_DELAYED":
            return await self.setSensor(self.MODE_AWAY_PUT_PATH, 1)
        elif mode == "HOME":
            return await self.setSensor(self.MODE_HOME_HIGH_CAL_PUT_PATH, 3)
        elif mode == "HIGH":
            return await self.setSensor(self.MODE_HOME_HIGH_CAL_PUT_PATH, 4)
        elif mode == "HIGH_ONTIMER":
            return await self.setSensor(self.MODE_HIGH_TEMP_PUT_PATH, 2)
        elif mode == "FIREPLACE":
            return await self.setSensor(self.MODE_FIREPLACE_PUT_PATH, 2)
        else:
            return False

    async def setFireplaceDuration(self, duration):
        return await self.setSensor(self.FIREPLACE_DURATION_PATH, duration)

    async def setBoostDuration(self, duration):
        return await self.setSensor(self.BOOST_DURATION_PATH, duration)

    async def setAwayDelay(self, delay):
        return await self.setSensor(self.AWAY_DELAY_PATH, delay)

    async def setHeaterState(self, heater_bool: bool) -> bool:
        return await self.setSensor(self.HEATER_PATH, 1 if heater_bool else 0)

    async def setCalendarActive(self):
        null = None
        return await self.setSensor(self.MODE_HOME_HIGH_CAL_PUT_PATH, null)

    async def setCalendarTemporaryOverride(self, value):
        return await self.setSensor(self.CALENDAR_TEMPORARY_OVERRIDE_PATH, value)
