#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import urllib.parse
from pprint import pprint

import arrow
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


DEFAULT_TIMEOUT = 20 # seconds
class TimeoutHTTPAdapter(HTTPAdapter):

    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)
    
class FlexitGo:

    def __init__(self):

        # Put paths
        self.MODE_AWAY_PUT_PATH                 = ";1!005000032000055"
        self.MODE_HOME_HIGH_CAL_PUT_PATH        = ";1!01300002A000055"
        self.MODE_HIGH_TEMP_PUT_PATH            = ";1!013000165000055"  # TOGGLES
        self.MODE_FIREPLACE_PUT_PATH            = ";1!013000168000055"  # TOGGLES

        self.FIREPLACE_DURATION_PATH            = ";1!03000010E000055"  # PUT AND GET
        self.BOOST_DURATION_PATH                = ";1!030000125000055"  # PUT AND GET
        self.AWAY_DELAY_PATH                    = ";1!03000013E000055"  # PUT AND GET
        self.CALENDAR_TEMPORARY_OVERRIDE_PATH   = ";1!0050001DA000055"  # PUT AND GET

        # Paths
        self.HOME_AIR_TEMPERATURE_PATH          = ";1!0020007CA000055"
        self.AWAY_AIR_TEMPERATURE_PATH          = ";1!0020007C1000055"
        self.ROOM_TEMPERATURE_PATH              = ";1!00000004B000055"
        self.CURRENT_FIREPLACE_DURATION_PATH    = ";1!0020007F6000055"
        self.CURRENT_BOOST_DURATION_PATH        = ";1!0020007EF000055"

        # Null*Off*Away*Home*High*Cocker hood*Fire place*Forced ventilation
        self.MODE_PATH                          = ";1!013000169000055"  # Null*Off*Away*Home*High*Cocker hood*Fire place*Forced ventilation
        self.OUTSIDE_AIR_TEMPERATURE_PATH       = ";1!000000001000055"  # Uteluft
        self.SUPPLY_AIR_TEMPERATURE_PATH        = ";1!000000004000055"  # Tilluft
        self.EXTRACT_AIR_TEMPERATURE_PATH       = ";1!00000003B000055"  # Avtrekk
        self.EXHAUST_AIR_TEMPERATURE_PATH       = ";1!00000000B000055"  # Avkast
        self.HEATER_PATH                        = ";1!0050001BD000055"
        self.FILTER_OPERATING_TIME_PATH         = ";1!00200011D000055"
        self.FILTER_TIME_FOR_EXCHANGE_PATH      = ";1!00200011E000055"
        self.ALARM_CODE_A_PATH                  = ";1!002000008000055"
        self.ALARM_CODE_B_PATH                  = ";1!002000082000055"

        self.HEAT_EXCHANGER_SPEED_PATH          = ";1!001000000000055"
        self.SUPPLY_FAN_SPEED_PATH              = ";1!000000005000055"
        self.SUPPLY_FAN_CONTROL_SIGNAL_PATH     = ";1!001000003000055"
        self.EXTRACT_FAN_SPEED_PATH             = ";1!00000000C000055"
        self.EXTRACT_FAN_CONTROL_SIGNAL_PATH    = ";1!001000004000055"
        self.ADDITIONAL_HEATER_PATH             = ";1!00100001D000055"

        self.OFFLINE_ONLINE_PATH                = ";0!Online"
        self.LAST_RESTART_REASON_PATH           = ";0!0083FFFFF0000C4"
        self.SYSTEM_STATUS_PATH                 = ";0!0083FFFFF000070"

        self.APPLICATION_SOFTWARE_VERSION_PATH  = ";0!0083FFFFF00000C"
        self.DEVICE_DESCRIPTION_PATH            = ";0!0083FFFFF00001C"
        self.MODEL_NAME_PATH                    = ";0!0083FFFFF000046"
        self.MODEL_INFORMATION_PATH             = ";0!0083FFFFF0012DB"
        self.SERIAL_NUMBER_PATH                 = ";0!0083FFFFF0013EC"
        self.FIRMWARE_REVISION_PATH             = ";0!0083FFFFF00002C"
        self.BACNET_MAC_PATH                    = ";0!108000000001313"
        self.DEVICE_FEATURES_PATH               = ";0!0083FFFFF0013F4"

        self.SENSOR_DATA_PATH_LIST = [
            self.MODE_PATH,
            self.MODE_HOME_HIGH_CAL_PUT_PATH,
            self.OUTSIDE_AIR_TEMPERATURE_PATH,
            self.SUPPLY_AIR_TEMPERATURE_PATH,
            self.EXTRACT_AIR_TEMPERATURE_PATH,
            self.EXHAUST_AIR_TEMPERATURE_PATH,
            self.HOME_AIR_TEMPERATURE_PATH,
            self.AWAY_AIR_TEMPERATURE_PATH,
            self.ROOM_TEMPERATURE_PATH,
            self.FILTER_OPERATING_TIME_PATH,
            self.FILTER_TIME_FOR_EXCHANGE_PATH,
            self.HEATER_PATH,
            self.HEAT_EXCHANGER_SPEED_PATH,
            self.SUPPLY_FAN_SPEED_PATH,
            self.SUPPLY_FAN_CONTROL_SIGNAL_PATH,
            self.EXTRACT_FAN_SPEED_PATH,
            self.EXTRACT_FAN_CONTROL_SIGNAL_PATH,
            self.ADDITIONAL_HEATER_PATH,
            self.ALARM_CODE_A_PATH,
            self.ALARM_CODE_B_PATH,
            self.BOOST_DURATION_PATH,
            self.FIREPLACE_DURATION_PATH,
            self.AWAY_DELAY_PATH,
            self.CALENDAR_TEMPORARY_OVERRIDE_PATH
        ]

        self.DEVICE_INFO_PATH_LIST = [
            self.APPLICATION_SOFTWARE_VERSION_PATH,
            self.DEVICE_DESCRIPTION_PATH,
            self.MODEL_NAME_PATH,
            self.MODEL_INFORMATION_PATH,
            self.SERIAL_NUMBER_PATH,
            self.FIRMWARE_REVISION_PATH,
            self.OFFLINE_ONLINE_PATH,
            self.SYSTEM_STATUS_PATH,
            self.LAST_RESTART_REASON_PATH,
        ]

        self.API_URL = "https://api.climatixic.com"
        self.TOKEN_PATH = f"{self.API_URL}/Token"
        self.PLANTS_PATH = f"{self.API_URL}/Plants"
        self.DATAPOINTS_PATH = f"{self.API_URL}/DataPoints"
        #self.FILTER_PATH = f"{self.DATAPOINTS_PATH}/Values?filterId="
        self.VALUES_PATH = f"{self.DATAPOINTS_PATH}/Values"

        self.session = requests.Session()

        assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
        self.session.hooks["response"].append(assert_status_hook)

        retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "¨TRACE", "POST"])

        self.session.mount("http://", TimeoutHTTPAdapter(max_retries=retry_strategy))
        self.session.mount("https://", TimeoutHTTPAdapter(max_retries=retry_strategy))

        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-us",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Flexit%20GO/2.0.6 CFNetwork/1128.0.1 Darwin/19.6.0",
            "Ocp-Apim-Subscription-Key": "c3fc1f14ce8747588212eda5ae3b439e",
            "Host": "api.climatixic.com"
            }


    def _path(self, path):
        return f"{self.plantId}{path}"


    def _escaped_filter_url(self, path):
        return f"{self.FILTER_PATH}{urllib.parse.quote(path)}"


    #def _create_url_from_paths(self, paths):
    #    url = "["
    #    for path in paths:
    #        url += f"""{{"DataPoints":"{self._path(path)}"}}{ "," if path != paths[-1] else "]"}"""
    #    return url


    def _create_url_from_paths2(self, paths):
        url = list()
        for path in paths:
            sub = {"DataPoints" : self._path(path)}
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
        if (self._present_priority(path) == 15):
            return True
        else:
            return False


    def _dirty_filter(self, filter_time_for_exchange):
        if arrow.get(filter_time_for_exchange) >= arrow.now():
            return False
        else:
            return True


    def _ventilation_mode(self, ventilation_int):
        mode = {
            0: "Null",
            1: "OFF",
            2: "AWAY",
            3: "HOME",
            4: "HIGH",
            5: "COOKER_HOOD",
            6: "FIREPLACE",
            7: "HIGH_DELAYED"
        }

        return mode.get(ventilation_int,f"Unknown mode: {str(ventilation_int)}")



    def _to_efficiency(self, tilluft, uteluft, frånluft):
        return round(((tilluft - uteluft)/(frånluft - uteluft)) * 100, 1)


    def _from_efficiency(self, uteluft, frånluft, avluft):
        return round(((frånluft - avluft)/(frånluft - uteluft)) *100, 1)


    def _validateToken(self):

        now = arrow.now("Europe/Stockholm")
        if now >= self.tokenValidTo.shift(hours=-1):
            print("Token about to expire loggin in again")
            self.login(self.username, self.password)


    def login(self, user, password):
        self.username = user
        self.password = password

        data = f"grant_type=password&username={self.username}&password={self.password}"

        try:
            response = self.session.post("https://api.climatixic.com/Token", headers=self.headers, data=data)
            #out = json.loads(response.text)
            out = response.json()

            access_token = f"Bearer {out['access_token']}"
            self.headers["Authorization"] = access_token
            fmt = "ddd, DD MMM YYYY HH:mm:ss ZZZ"
            self.tokenValidTo = arrow.get(out[".expires"], fmt).to("Europe/Stockholm")
            self.getPlant()

            return out

        except Exception as e:
            print(e)


    def getPlant(self):
        out = dict()
        try:
            response = self.session.get("https://api.climatixic.com/Plants", headers=self.headers)
            out = response.json()

            for d in out["items"]:
                self.plantId = d["id"]

        except Exception as e:
            print(e)

        return out


    def getDevice(self):
        out = dict()
        #url = self._escaped_filter_url(self._create_url_from_paths(self.DEVICE_INFO_PATH_LIST))
        paramlist = self._create_url_from_paths2(self.DEVICE_INFO_PATH_LIST)
        param = {
                "filterId": json.dumps(paramlist, separators=(',', ':'))
                }

        try:
            response = self.session.get(self.VALUES_PATH, headers=self.headers, params=param)
            self.deviceData = response.json()

            #pprint(self.deviceData)

            out["fw"] = self._str_device(self.FIRMWARE_REVISION_PATH)
            out["modelName"] = self._str_device(self.MODEL_NAME_PATH)
            out["modelInfo"] = self._str_device(self.MODEL_INFORMATION_PATH)
            out["serialInfo"] = self._str_device(self.SERIAL_NUMBER_PATH)
            out["systemStatus"] = self._str_device(self.SYSTEM_STATUS_PATH)
            out["status"] = self._str_device(self.OFFLINE_ONLINE_PATH)
            out["deviceDescription"] = self._str_device(self.DEVICE_DESCRIPTION_PATH)
            out["applicationSoftwareVersion"] = self._str_device(self.APPLICATION_SOFTWARE_VERSION_PATH)
            out["lastRestartReason"] = self._int_device(self.LAST_RESTART_REASON_PATH)

        except Exception as e:
            print(e)

        return out


    def getSensors(self):
        self._validateToken()
        out = dict()
        #url1 = self._escaped_filter_url(self._create_url_from_paths(self.SENSOR_DATA_PATH_LIST))
        paramlist = self._create_url_from_paths2(self.SENSOR_DATA_PATH_LIST)
        param = {
                "filterId": json.dumps(paramlist, separators=(',', ':'))
                }

        try:
            response = self.session.get(self.VALUES_PATH, headers=self.headers, params=param)
            self.sensorData = response.json()

            #pprint(self.sensorData)

            out["temps"] = dict()
            out["fläkt"] = dict()
            out["filter"] = dict()
            out["alarm"] = dict()
            out["modes"] = dict()

            out["temps"]["home_air_temperature"] = self._float_sensor(self.HOME_AIR_TEMPERATURE_PATH)
            out["temps"]["away_air_temperature"] = self._float_sensor(self.AWAY_AIR_TEMPERATURE_PATH)
            out["temps"]["Uteluft"]  = self._float_sensor(self.OUTSIDE_AIR_TEMPERATURE_PATH)
            out["temps"]["Tilluft"]  = self._float_sensor(self.SUPPLY_AIR_TEMPERATURE_PATH)
            out["temps"]["Avluft"]  = self._float_sensor(self.EXHAUST_AIR_TEMPERATURE_PATH)
            out["temps"]["Frånluft"]  = self._float_sensor(self.EXTRACT_AIR_TEMPERATURE_PATH)
            out["temps"]["room_temperature"]  = self._float_sensor(self.ROOM_TEMPERATURE_PATH)
            out["modes"]["electric_heater"]  = self._bool_sensor(self.HEATER_PATH)
            out["modes"]["ventilation_mode"]  = self._ventilation_mode(self._int_sensor(self.MODE_PATH))
            out["modes"]["ventilation_mode_cal"]  = self._ventilation_mode(self._int_sensor(self.MODE_HOME_HIGH_CAL_PUT_PATH))
            out["modes"]["heat_exchanger_speed"] = self._int_sensor(self.HEAT_EXCHANGER_SPEED_PATH)
            out["fläkt"]["supply_fan_speed"]  = self._int_sensor(self.SUPPLY_FAN_SPEED_PATH)
            out["fläkt"]["supply_fan_control_signal"]  = self._float_sensor(self.SUPPLY_FAN_CONTROL_SIGNAL_PATH)
            out["fläkt"]["extract_fan_speed"]  = self._int_sensor(self.EXTRACT_FAN_SPEED_PATH)
            out["fläkt"]["extract_fan_control_signal"]  = self._float_sensor(self.EXTRACT_FAN_CONTROL_SIGNAL_PATH)
            out["modes"]["additional_heater"]  = self._bool_sensor(self.ADDITIONAL_HEATER_PATH)
            out["alarm"]["alarm_code_a"]  = self._int_sensor(self.ALARM_CODE_A_PATH)
            out["alarm"]["alarm_code_b"]  = self._int_sensor(self.ALARM_CODE_B_PATH)
            out["modes"]["calendar_temporary_override"]  = self._bool_sensor(self.CALENDAR_TEMPORARY_OVERRIDE_PATH)
            out["modes"]["calendar_active"] = self._calendar_active(self.MODE_HOME_HIGH_CAL_PUT_PATH)
            out["modes"]["boost_duration"] = self._int_sensor(self.BOOST_DURATION_PATH)
            out["modes"]["away_delay"]  = self._int_sensor(self.AWAY_DELAY_PATH)
            out["modes"]["fireplace_duration"]  = self._int_sensor(self.FIREPLACE_DURATION_PATH)

            out["temps"]["verkningsgrad_tilluft"] = self._to_efficiency(out["temps"]["Tilluft"], out["temps"]["Uteluft"], out["temps"]["Frånluft"])
            out["temps"]["verkningsgrad_frånluft"] = self._from_efficiency(out["temps"]["Uteluft"], out["temps"]["Frånluft"], out["temps"]["Avluft"])

            now = arrow.now()
            out["filter"]["filter_exchanged"]  = now.shift(hours= -self._int_sensor(self.FILTER_OPERATING_TIME_PATH)).format("YYYY-MM-DD")
            out["filter"]["filter_time_for_exchange"]  = now.shift(hours=self._int_sensor(self.FILTER_TIME_FOR_EXCHANGE_PATH)-self._int_sensor(self.FILTER_OPERATING_TIME_PATH)).format("YYYY-MM-DD")
            out["filter"]["dirty_filter"]  = self._dirty_filter(out["filter"]["filter_time_for_exchange"])

        except Exception as e:
            print(e)

        return out


    def setSensor(self, path, body):
        data_body = null if body is None else str(body)
        url=self._escaped_datapoints_url(self._path(path))
        data=json.dumps({"Value": data_body})

        try:
            response = self.session.put(url, headers=self.headers, data=data)
            out = response.json()

            return out["stateTexts"][self._path(path)] == "Success"

        except Exception as e:
            print(e)
            return False


    def setHomeTemp(self, temp):
        return self.setSensor(self.HOME_AIR_TEMPERATURE_PATH, temp)


    def setAwayTemp(self, temp):
        return self.setSensor(self.AWAY_AIR_TEMPERATURE_PATH, temp)


    def setPresetMode(self, presetMode):

        acceptedModes = ["HOME", "AWAY", "AWAY_DELAYED", "HIGH", "HIGH_ONTIMER", "FIREPLACE"]

        if (presetMode not in acceptedModes):
            print(f"{presetMode} are not a valid  mode!")
            return False

        currentMode = self.getSensors()["modes"]["ventilation_mode"]
        result = list()

        if (currentMode == presetMode):
            return

        # Toggle modes that requires toggle
        toggleChange = {
                "AWAY": "AWAY_DELAYED",
                "HIGH_ONTIMER": "HIGH_ONTIMER",
                "FIREPLACE": "FIREPLACE"
                }
        if currentMode in toggleChange:
            result.append(self._setMode(toggleChange[currentMode]))
            print(f"switching från {currentMode} to {toggleChange[currentMode]}")

        result.append(self._setMode(presetMode))
        print(f"switching mode to {presetMode}")

        return all(result)


    def _setMode(self, mode):
        if mode == "AWAY":
            return self.setSensor(self.MODE_AWAY_PUT_PATH, 0)
        elif mode == "AWAY_DELAYED":
            return self.setSensor(self.MODE_AWAY_PUT_PATH, 1)
        elif mode == "HOME":
            return self.setSensor(self.MODE_HOME_HIGH_CAL_PUT_PATH, 3)
        elif mode == "HIGH":
            return self.setSensor(self.MODE_HOME_HIGH_CAL_PUT_PATH, 4)
        elif mode == "HIGH_ONTIMER":
            return self.setSensor(self.MODE_HIGH_TEMP_PUT_PATH, 2)
        elif mode == "FIREPLACE":
            return self.setSensor(self.MODE_FIREPLACE_PUT_PATH, 2)
        else:
            return False


    def setFireplaceDuration(self, duration):
        return self.setSensor(self.FIREPLACE_DURATION_PATH, duration)


    def setBoostDuration(self, duration):
        return self.setSensor(self.BOOST_DURATION_PATH, duration)


    def setAwayDelay(self, delay):
        return self.setSensor(self.AWAY_DELAY_PATH, delay)


    def setHeaterState(self, heater_bool: bool) -> bool:
        return self.setSensor(self.HEATER_PATH, 1 if heater_bool else 0)


    def setCalendarActive(self):
        null = None
        return self.setSensor(self.MODE_HOME_HIGH_CAL_PUT_PATH, null)


    def setCalendarTemporaryOverride(self, value):
        return self.setSensor(self.CALENDAR_TEMPORARY_OVERRIDE_PATH, value)
