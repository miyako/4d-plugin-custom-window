If (Form event code:C388=On Load:K2:1)
	SET WINDOW ALPHA (Current form window:C827;1;1)
End if 

If (Form event code:C388=On Timer:K2:25)
	SET TIMER:C645(0)
	ACCEPT:C269
End if 