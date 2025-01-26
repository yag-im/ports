@rem INNOCENT until caught
@rem PC CD
@rem (c) 1994 Divide By Zero
@
@echo off
language
if errorlevel 5 goto italian
if errorlevel 4 goto spanish
if errorlevel 3 goto french
if errorlevel 2 goto german
if errorlevel 1 goto english
goto end

:english
if exist c:\innocent\innocent.ini goto run_english
set_eng
:run_english
english %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:german
if exist c:\innocent\innocent.ini goto run_german
set_dtl
:run_german
german %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:french
if exist c:\innocent\innocent.ini goto run_french
set_frn
:run_french
french %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:spanish
if exist c:\innocent\innocent.ini goto run_spanish
set_esp
:run_spanish
spanish %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:italian
if exist c:\innocent\innocent.ini goto run_italian
set_itl
:run_italian
italian %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:end
EXIT
