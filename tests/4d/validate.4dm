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

var $handle : cs:C1710.uzu
$handle:=cs:C1710.uzu.new()

File:C1566(Structure file:C489; fk platform path:K87:2).parent.parent.file("regressions.json").setText(\
	JSON Stringify:C1217({success: $failures.length=0; failures: $failures}; *))
QUIT 4D:C291
