# 4d-plugin-custom-window
Set window transparent on Mac 64-bit

###Platform

| carbon | cocoa | win32 | win64 |
|:------:|:-----:|:---------:|:---------:|
|🆗|🆗|🚫|🚫|

###Version

<img src="https://cloud.githubusercontent.com/assets/1725068/18940649/21945000-8645-11e6-86ed-4a0f800e5a73.png" width="32" height="32" /> <img src="https://cloud.githubusercontent.com/assets/1725068/18940648/2192ddba-8645-11e6-864d-6d5692d55717.png" width="32" height="32" />

Parameter|Type|Description
------------|------|----
window|IN32|The window reference

###Example

```
If (Form event=On Load)
	SET WINDOW TRANSPARENT (Current form window)
End if 
```
