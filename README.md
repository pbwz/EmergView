# EmergView
EmergView is an application that tries to estimate AHS emergency room wait times across the province using an API.
Using this data, EmergView's algorithm can attempt to predict future wait times at any of the hospitals across 
the province. EmergView also has the functionality to recommend a hospital emergency room basedoff of a given
location and traffic data collected from an API.

**Please note: Development relies on statistical analysis of collected data thus will be slow**

# Information
EmergView runs in two parts:
  - An script running on a server or Raspberry Pi that requests AHS emergency data every 5 minutes and collects the data.
  - A secondary GUI based program containing the algorithms needed to interpret the aforementioned data.

## DISCLAIMER ##
While the goal of this project is to predict emergency room wait times and predict optimal hospital routes at
a given time, this data is meant for educational purposes and **SHOULD NOT BE USED IN ACTUAL EMERGENCY SITUATIONS**!

**If you are in need of emergency medical assitance, please call 911**
