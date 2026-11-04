property model : 4D:C1709.Folder
property _started : Boolean

Class extends _models

Class constructor($port : Integer; $huggingfaces : cs:C1710.event.huggingfaces; $options : Object; $formula : 4D:C1709.Function; $event : cs:C1710.event.event)
	
	Super:C1705($port; $huggingfaces; $options; $formula; $event)
	
	If (Not:C34(This:C1470.offline))
		This:C1470.download()
	End if 
	
Function models() : cs:C1710.event.models
	
	var $model : cs:C1710.event.model
	
	Case of 
		: (Value type:C1509(This:C1470.options.model)=Is object:K8:27)
			$model:=cs:C1710.event.model.new(This:C1470.options.model.name; Not:C34(This:C1470.options.model.exists))
			return cs:C1710.event.models.new([$model])
			
		: (Value type:C1509(This:C1470.options.model)=Is collection:K8:32)
			var $models : Collection
			$models:=[]
			For each ($_model; This:C1470.options.model)
				$model:=cs:C1710.event.model.new($_model.name; Not:C34($_model.exists))
				$models.push($model)
			End for each 
			return cs:C1710.event.models.new($models)
			
		: (Value type:C1509(This:C1470.options.model)=Is text:K8:3)
			//cli downloads the model
			return cs:C1710.event.models.new([cs:C1710.event.model.new()])
	End case 
	
Function onDownload($oid : Text)
	
	If (This:C1470.options.model=Null:C1517)
		var $downloaded : cs:C1710.event.huggingface
		$downloaded:=This:C1470.files.query("oid == :1"; $oid).first()
		If ($downloaded#Null:C1517)
			var $model : Object
			$model:=$downloaded.folder
			
			//any file not in option is assumed to be the main model
			var $option : Text
			var $match : Boolean
			$match:=False:C215
			
			For each ($option; This:C1470.options)
				var $value : Variant
				$value:=This:C1470.options[$option]
				var $vt : Integer
				$vt:=Value type:C1509($value)
				If ($vt#Is object:K8:27)
					continue
				End if 
				If (Not:C34(OB Instance of:C1731($value; 4D:C1709.File)))
					continue
				End if 
				If ($model.path=("@"+$value.fullName))
					$match:=True:C214
					break
				End if 
			End for each 
			
			If (Not:C34($match))
				This:C1470.options.model:=$model
			End if 
		End if 
	End if 
	
	Super:C1706.onDownload($oid)
	
Function _onNothingToDownload()

	If (OB Instance of:C1731(This:C1470.options.model; 4D:C1709.Folder))
		If (This:C1470.options.model.exists)
			This:C1470.start()
			return
		End if
	End if
	var $message : Text
	$message:="no model to load: nothing to download and options.model is not an existing folder"
	If (OB Instance of:C1731(This:C1470.options.model; 4D:C1709.Folder))
		$message+=": "+This:C1470.options.model.path
	End if
	If (This:C1470._unresolved.length#0)
		$message+="; "+This:C1470._unresolved.join("; ")
	End if
	LOG EVENT:C667(Into 4D debug message:K38:5; "uzu: "+$message)
	This:C1470._notifyError(cs:C1710.event.error.new(2; $message; cs:C1710.event.models.new()))

Function start()
	
	If (This:C1470._started)
		return
	End if
	//uzu takes a model identifier or a complete model directory, never a single file
	var $hasModel : Boolean
	Case of
		: (Value type:C1509(This:C1470.options.model)=Is text:K8:3)
			$hasModel:=(This:C1470.options.model#"")
		: (OB Instance of:C1731(This:C1470.options.model; 4D:C1709.Folder))
			$hasModel:=This:C1470.options.model.exists
	End case
	If (Not:C34($hasModel))
		var $message : Text
		$message:="no model to load: options.model is not a model identifier or an existing folder"
		If (OB Instance of:C1731(This:C1470.options.model; 4D:C1709.Folder)) || (OB Instance of:C1731(This:C1470.options.model; 4D:C1709.File))
			$message+=": "+This:C1470.options.model.path
		End if
		LOG EVENT:C667(Into 4D debug message:K38:5; "uzu: "+$message)
		This:C1470._notifyError(cs:C1710.event.error.new(2; $message; cs:C1710.event.models.new()))
		return
	End if
	This:C1470._started:=True:C214
	var $uzu : cs:C1710.workers.worker
	$uzu:=cs:C1710.workers.worker.new(cs:C1710._server)
	$uzu.start(This:C1470.options.port; This:C1470.options)
	
	If (This:C1470.event#Null:C1517) && (OB Instance of:C1731(This:C1470.event; cs:C1710.event.event))
		This:C1470.event.onSuccess.call(This:C1470; This:C1470.options; This:C1470.models())
	End if 