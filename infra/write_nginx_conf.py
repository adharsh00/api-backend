"""Write the nginx app.conf to the EC2 instance via SSH stdin pipe."""
import subprocess

NGINX_CONF = r"""server {
    listen 80;
    root /home/ec2-user/api-backend/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
"""

pem = r"E:\adharsh_api\cloud-key-pair.pem"
host = "ec2-user@54.247.232.118"

proc = subprocess.run(
    ["ssh", "-i", pem, "-o", "StrictHostKeyChecking=no", host,
     "sudo tee /etc/nginx/conf.d/app.conf"],
    input=NGINX_CONF.encode(),
    capture_output=True,
)
print("rc:", proc.returncode)
if proc.stdout:
    print(proc.stdout.decode())
if proc.stderr:
    print("STDERR:", proc.stderr.decode())
print("Done" if proc.returncode == 0 else "FAILED")
