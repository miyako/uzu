property model : 4D:C1709.Folder

Class extends _models

Class constructor($port : Integer; $huggingfaces : cs:C1710.event.huggingfaces; $options : Object; $formula : 4D:C1709.Function; $event : cs:C1710.event.event)
	
	Super:C1705($port; $huggingfaces; $options; $formula; $event)
	
	If (Not:C34(This:C1470.offline))
		This:C1470.download()
	End if 
	
Function _isRouterMode() : Boolean
	
	return ((OB Instance of:C1731(This:C1470.options.models_preset; 4D:C1709.File))\
		 && (This:C1470.options.models_preset.exists))\
		 || ((OB Instance of:C1731(This:C1470.options.models_dir; 4D:C1709.Folder))\
		 && (This:C1470.options.models_dir.exists))
	
Function models() : cs:C1710.event.models
	
	If (This:C1470._isRouterMode())
		return cs:C1710.event.models.new([cs:C1710.event.model.new()])
	End if 
	
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
			$model:=OB Instance of:C1731($downloaded.folder; 4D:C1709.Folder)\
				 ? $downloaded.folder.file($downloaded.path) : $downloaded.folder
			
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
	
Function start()
	
	var $uzu : cs:C1710.workers.worker
	$uzu:=cs:C1710.workers.worker.new(cs:C1710._server)
	$uzu.start(This:C1470.options.port; This:C1470.options)
	
	If (This:C1470.event#Null:C1517) && (OB Instance of:C1731(This:C1470.event; cs:C1710.event.event))
		This:C1470.event.onSuccess.call(This:C1470; This:C1470.options; This:C1470.models())
	End if 