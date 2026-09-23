class InterfaceTaskInfo extends GSInfo {
    function GetAuthor()      { return "Agent Interface research"; }
    function GetName()        { return "InterfaceTask"; }
    function GetDescription() { return "Read-only L-road benchmark observer"; }
    function GetVersion()     { return 1; }
    function GetDate()        { return "2026-09-14"; }
    function CreateInstance() { return "InterfaceTask"; }
    function GetShortName()   { return "AITL"; }
    function GetAPIVersion()  { return "13"; }
}
RegisterGS(InterfaceTaskInfo());
