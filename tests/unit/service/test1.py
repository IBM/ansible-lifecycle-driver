# import logging
import unittest
# import time
# import uuid
# import shutil
# import os
# import base64
import json
from unittest.mock import patch, MagicMock, ANY
# from ansibledriver.service.ansible import AnsibleClient
# from ignition.utils.file import DirectoryTree

class Test1(unittest.TestCase):

    def test1(self):
        # root = DirectoryTree('.')
        # print(root.get_file_path('.'))

      # props = {
      #   'output__prop1': 'value1',
      #   'prop2': 'value2'
      # }
      # props = { key:value for key, value in props.items() if key.startswith("output__") }
      # print(props)

      # print("output__prop1"[8:])

    # def test1(self):
    #   str = 'UEsDBBQACAgIALeJyk4AAAAAAAAAAAAAAAAJAAAAaW52ZW50b3J5iy5JLS7JyC8uieUCsXRBTABQSwcIb+K2OhEAAAAUAAAAUEsDBBQACAgIALeJyk4AAAAAAAAAAAAAAAAXAAAAaG9zdF92YXJzL3Rlc3QtaG9zdC55bWyFjkEKgCAURPedwgt4gS4jph8UzC9+q4V491QoJBdt37wZhnO+SE92cyAMUlpZzsyAcygujE6LEO0pEwgbWCmvqtB7UMmiXxmReflBEPvEA2rY4Vh+2K8YJFF9oSexBd/Fxn7FDRTuMLsDr/oNUEsHCKdsam5tAAAAFQEAAFBLAwQUAAgICAC3icpOAAAAAAAAAAAAAAAADAAAAGluc3RhbGwueWFtbG2LwQ3DIAxF753CC3SBrJEBLAhWsAQYYZMoirJ7adVcqv7je+8/IZDv6/SAsazrBPOhRhnOE7hsVEzagVHUissE1wXRKfTO4V24ouwTYW0S+mL44aMZKlJKgru0FIbmzRkh16+8f6oRu1L7g6tT/cGeFsl0mxdQSwcIDepDOXYAAAC6AAAAUEsBAhQAFAAICAgAt4nKTm/itjoRAAAAFAAAAAkAAAAAAAAAAAAAAAAAAAAAAGludmVudG9yeVBLAQIUABQACAgIALeJyk6nbGpubQAAABUBAAAXAAAAAAAAAAAAAAAAAEgAAABob3N0X3ZhcnMvdGVzdC1ob3N0LnltbFBLAQIUABQACAgIALeJyk4N6kM5dgAAALoAAAAMAAAAAAAAAAAAAAAAAPoAAABpbnN0YWxsLnlhbWxQSwUGAAAAAAMAAwC2AAAAqgEAAAAA'

    #   with open('a.zip', 'wb') as writer:
    #     writer.write(base64.b64decode(str))


       with open(fname) as f:
         content = [x.strip() for x in f.readlines()]





       vpls_list = []
       name_list = ["mgmt-vlan", "voice-vlan"]
       int_list = ["mgmt-vlan-of0000000000000001-4",
                   "voice-vlan-of0000000000000001-4",
                   "mgmt-vlan-of0000000000000001-5",
                   "voice-vlan-of0000000000000001-5",
                   "mgmt-vlan-of0000000000000001-6",
                   "voice-vlan-of0000000000000001-6",
                   "mgmt-vlan-of0000000000000002-4",
                   "voice-vlan-of0000000000000002-4",
                   "mgmt-vlan-of0000000000000002-5",
                   "voice-vlan-of0000000000000002-5",
                   "mgmt-vlan-of0000000000000002-6",
                   "voice-vlan-of0000000000000002-6"]

       # print([inf for inf in int_list if inf.startswith("mgmt-vlan")])

       for name in name_list:
         vpls_list.append({
           "name": name,
           "interfaces": [inf for inf in int_list if inf.startswith(name)]
         })

       with open('/tmp/x', 'w') as f:
         f.write(json.dumps({
           "apps" : {
             "org.onosproject.vpls" : {
               "vpls" : {
                 "vplsList" : vpls_list
               }
             }
           }}))
