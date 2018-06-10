#bash
#Se puede encontrar en el journal cuando se ejecuta este script con journalctl -t portfolio
echo 'Actualizando porfolio' | systemd-cat -t portfolio -p info
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/app/ portfolio@192.168.1.55:/home/portfolio/portfolio/app/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/chromedriver/ portfolio@192.168.1.55:/home/portfolio/portfolio/chromedriver/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/migrations/ portfolio@192.168.1.55:/home/portfolio/portfolio/migrations/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/config.py portfolio@192.168.1.55:/home/portfolio/portfolio/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/portfolio.py portfolio@192.168.1.55:/home/portfolio/portfolio/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/requirements.txt portfolio@192.168.1.55:/home/portfolio/portfolio/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/scrape.py portfolio@192.168.1.55:/home/portfolio/portfolio/
rsync --delete --progress --omit-dir-times --no-perms --stats -avz /home/daniel/proyectos/portfolio/XIRR.py portfolio@192.168.1.55:/home/portfolio/portfolio/