@rem Guilty
@rem PC CD
@rem (c) 1995 Divide By Zero
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
english %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:german
german %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:french
french %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:spanish
spanish %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:italian
italian %1 %2 %3 %4 %5 %6 %7 %8 %9
goto end

:end
EXIT
