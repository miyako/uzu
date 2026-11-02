//%attributes = {"invisible":true,"preemptive":"capable"}
#DECLARE($options : Object; $formula : 4D:C1709.Function)

var $model : cs:C1710._Model

If (Value type:C1509($options.options)#Is object:K8:27)
	$options.options:={}
End if

var $validModel : Boolean
Case of
	: (Value type:C1509($options.options.model)=Is text:K8:3)
		$validModel:=($options.options.model#"")
	: (OB Instance of:C1731($options.options.model; 4D:C1709.Folder))
		$validModel:=$options.options.model.exists
	: ($options.options.model=Null:C1517)
		$validModel:=($options.huggingfaces.huggingfaces.length#0)
End case

If (Not:C34($validModel))
	var $error : cs:C1710.event.error
	$error:=cs:C1710.event.error.new(2; "Uzu requires options.model: a model identifier, repository ID or complete local model directory.")
	If (OB Instance of:C1731($options.event; cs:C1710.event.event))
		$options.event.onError.call(This:C1470; $options; $error)
	Else
		LOG EVENT:C667(Into 4D debug message:K38:5; $error.message)
	End if
	return
End if

$model:=cs:C1710._Model.new($options.port; $options.huggingfaces; $options.options; $formula; $options.event)

If ($model.offline)
	$model.start()
End if 