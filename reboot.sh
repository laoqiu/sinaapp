work_dir="/root/www/webapp/"
site_name="webapp"
sock="/tmp/webapp.sock"

if [ -f ${work_dir}${site_name}.pid ]; then
   echo stopping ${site_name} site
   kill `cat ${work_dir}${site_name}.pid`
   echo your site ${site_name} stoped
else
   echo ${site_name} was not running
fi

echo reboot your site ${site_name}

cd ${work_dir}
python fcgi.py method=prefork/threaded minspare=50 maxspare=50 maxchildren=1000 &

sleep 3

chown www-data:www-data ${sock}
 
ps aux | grep fcgi.py | grep -v grep | awk '{print $2}' > ${work_dir}${site_name}.pid

echo your site ${site_name} rebooted
echo starting nginx
service nginx start
cd -
