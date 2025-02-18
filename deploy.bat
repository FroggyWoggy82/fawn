@echo off
git add deploy.bat setup_db.bat & git commit -m "Update deploy.bat to use & for chaining and include setup_db.bat" & git push origin master & call setup_db.bat