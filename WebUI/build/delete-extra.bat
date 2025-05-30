@echo off
setlocal

REM This script deletes all the extra environments and directories created during the setup.
echo Deleting extra environments and directories...

rmdir /s /q ai-backend-env
rmdir /s /q openvino-env
rmdir /s /q comfyui-backend-env
rmdir /s /q _aipg_apps
rmdir /s /q prototype-python-env

endlocal