//%attributes = {}
var $failures : Collection
$failures:=[]
var $event : cs:C1710.event.event
$event:=cs:C1710.event.event.new()
var $huggingfaces : cs:C1710.event.huggingfaces
$huggingfaces:=cs:C1710.event.huggingfaces.new([])
var $models : cs:C1710._models

$models:=cs:C1710._models.new(8080; $huggingfaces; \
	{model: "alibaba:qwen3.5:0.8b:mirai:mirai-m:4"}; Null:C1517; $event)
If (Not:C34($models.offline)) || ($models.files.length#0)
	$failures.push("Catalog identifiers must delegate to Uzu without component downloads")
End if

$models:=cs:C1710._models.new(8080; $huggingfaces; \
	{model: "trymirai/Qwen3.5-0.8B-L"}; Null:C1517; $event)
If (Not:C34($models.offline))
	$failures.push("Repository identifiers must still delegate to Uzu")
End if

var $folder : 4D:C1709.Folder
$folder:=File:C1566(Structure file:C489; fk platform path:K87:2).parent
$models:=cs:C1710._models.new(8080; $huggingfaces; \
	{model: $folder}; Null:C1517; $event)
If (Not:C34($models.offline))
	$failures.push("Existing local folders must bypass the component download queue")
End if

$models:=Try(cs:C1710._models.new(8080; $huggingfaces; \
	{model: "trymirai/Qwen3.5-0.8B-L"}; Null:C1517; Null:C1517))
If ($models=Null:C1517) || (Last errors:C1799#Null:C1517)
	$failures.push("A Null event must not raise in the _models constructor")
End if

var $reported : Object
$reported:={errors: []}
var $reporting : cs:C1710.event.event
$reporting:=cs:C1710.event.event.new()
$reporting.onError:=Formula:C1597($reported.errors.push($2))
var $model : cs:C1710._Model
$model:=cs:C1710._Model.new(8080; cs:C1710.event.huggingfaces.new([]); {}; Null:C1517; $reporting)
If ($reported.errors.length#1) || ($reported.errors[0].code#2)
	$failures.push("Nothing to download without a local model folder must report onError code 2 and not launch")
End if

$reported.errors.clear()
$model:=cs:C1710._Model.new(8080; cs:C1710.event.huggingfaces.new([]); {model: "trymirai/Qwen3.5-0.8B-L"}; Null:C1517; $reporting)
$model.options.model:=$folder.folder("missing-model-folder")
$model.start()
If ($reported.errors.length#1) || ($reported.errors[0].code#2)
	$failures.push("Starting with a nonexistent model folder (e.g. Hugging Face unreachable) must report onError code 2 and not launch")
End if

$reported.errors.clear()
var $weights : 4D:C1709.File
$weights:=Folder:C1567(Temporary folder:C486; fk platform path:K87:2).file("uzu-validate-"+Generate UUID:C1066+".bin")
$weights.setText("x")
$model:=cs:C1710._Model.new(8080; cs:C1710.event.huggingfaces.new([]); {model: "trymirai/Qwen3.5-0.8B-L"}; Null:C1517; $reporting)
$model.options.model:=$weights
$model.start()
$weights.delete()
If ($reported.errors.length#1) || ($reported.errors[0].code#2)
	$failures.push("A single 4D.File is not a uzu model and must report onError code 2 instead of launching")
End if

$reported.errors.clear()
$model:=cs:C1710._Model.new(8080; cs:C1710.event.huggingfaces.new([]); {}; Null:C1517; Null:C1517)
$model.event:=$reporting
$model._unresolved.push("user/repo: Hugging Face API returned HTTP 401")
$model.download()
If ($reported.errors.length#1) || (Position:C15("HTTP 401"; $reported.errors[0].message)=0)
	$failures.push("Skipped Hugging Face descriptors must be named in the onError message")
End if

If ([0.3; 32768; 0.00001].map(Formula:C1597(_argNumber($1.value))).join(" ")#"0.3 32768 1E-05")
	$failures.push("Numeric server arguments must use '.' regardless of the system locale")
End if

var $handle : cs:C1710.uzu
$handle:=cs:C1710.uzu.new()

File:C1566(Structure file:C489; fk platform path:K87:2).parent.parent.file("regressions.json").setText(\
	JSON Stringify:C1217({success: $failures.length=0; failures: $failures}; *))
QUIT 4D:C291
