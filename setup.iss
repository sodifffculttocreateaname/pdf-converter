; PDF工具箱 安装程序配置
; 使用 Inno Setup Compiler 编译此文件

[Setup]
AppId={{8A7F3B2C-9D5E-4A1B-8C3F-6E2D7A5B9C4E}
AppName=PDF工具箱
AppVersion=1.0.0
AppPublisher=PDF Tools
AppPublisherURL=https://github.com/example/pdf-tools
AppSupportURL=https://github.com/example/pdf-tools
AppUpdatesURL=https://github.com/example/pdf-tools
DefaultDirName={autopf}\PDF工具箱
DefaultGroupName=PDF工具箱
AllowNoIcons=yes
; 输出安装程序
OutputDir=installer
OutputBaseFilename=PDF工具箱_安装程序
; SetupIconFile=resources\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; 权限
PrivilegesRequired=admin
; 卸载
UninstallDisplayIcon={app}\PDF工具箱.exe
UninstallDisplayName=PDF工具箱
; 支持中文
LanguageDetectionMethod=locale

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 复制所有打包文件
Source: "dist\PDF工具箱\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PDF工具箱"; Filename: "{app}\PDF工具箱.exe"
Name: "{group}\卸载PDF工具箱"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PDF工具箱"; Filename: "{app}\PDF工具箱.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PDF工具箱.exe"; Description: "{cm:LaunchProgram,PDF工具箱}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"