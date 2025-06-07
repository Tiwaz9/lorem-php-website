# terraform/alb_asg.tf

# 1) Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  owners      = ["amazon"]
  most_recent = true
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# 2) Launch Template: NGINX, PHP-FPM, Git, clone app, configure with API URL
resource "aws_launch_template" "web_lt" {
  name_prefix   = "${var.project_name}-lt-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_instance_profile.name
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.ec2_sg.id]
    subnet_id                   = element(aws_subnet.private.*.id, 0)
  }

  user_data = base64encode(<<-EOF
#!/bin/bash

# Update and install packages
yum update -y
amazon-linux-extras enable nginx1 php7.4
yum clean metadata
yum install -y nginx php-fpm git

# Prepare webroot
dir="/var/www/lorem-app/public"
mkdir -p "$dir"
chown nginx:nginx "$dir"

# Clone the application code (public repo containing only the public/ folder)
cd /tmp
git clone --branch ${var.github_repo_branch} ${var.github_repo_url} repo

# Copy files from the 'public' directory of the repo into webroot
if [ -d /tmp/repo/public ]; then
  cp -r /tmp/repo/public/* "$dir"
elif [ -d /tmp/repo/app/public ]; then
  cp -r /tmp/repo/app/public/* "$dir"
else
  echo "Error: public directory not found in repo" >&2
fi

# Set correct ownership so NGINX can serve so NGINX can serve
chown -R nginx:nginx "$dir"

# Create NGINX configuration
echo 'server {' > /etc/nginx/conf.d/lorem.conf
echo '    listen       80;' >> /etc/nginx/conf.d/lorem.conf
echo '    server_name  _;' >> /etc/nginx/conf.d/lorem.conf
echo '    root         /var/www/lorem-app/public;' >> /etc/nginx/conf.d/lorem.conf
echo '    index        index.php index.html;' >> /etc/nginx/conf.d/lorem.conf

echo '    location / {' >> /etc/nginx/conf.d/lorem.conf
echo '        try_files $uri $uri/ /index.php$is_args$args;' >> /etc/nginx/conf.d/lorem.conf
echo '    }' >> /etc/nginx/conf.d/lorem.conf

echo '    location ~ \.php$ {' >> /etc/nginx/conf.d/lorem.conf
echo '        fastcgi_pass   unix:/var/run/php-fpm/www.sock;' >> /etc/nginx/conf.d/lorem.conf
echo '        fastcgi_index  index.php;' >> /etc/nginx/conf.d/lorem.conf
echo '        fastcgi_param  SCRIPT_FILENAME  /var/www/lorem-app/public$fastcgi_script_name;' >> /etc/nginx/conf.d/lorem.conf
echo '        fastcgi_param  INVENTORY_API_URL "https://${aws_api_gateway_rest_api.inventory_api.id}.execute-api.${var.aws_region}.amazonaws.com/prod/inventory";' >> /etc/nginx/conf.d/lorem.conf
echo '        include        fastcgi_params;' >> /etc/nginx/conf.d/lorem.conf
echo '    }' >> /etc/nginx/conf.d/lorem.conf

echo '}' >> /etc/nginx/conf.d/lorem.conf

# Enable and start services
systemctl enable php-fpm
systemctl start php-fpm
systemctl enable nginx
systemctl start nginx
EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-web-server"
    }
  }
}

# 3) Target Group
resource "aws_lb_target_group" "web_tg" {
  name     = "${var.project_name}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/index.php"
    protocol            = "HTTP"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
  }

  tags = {
    Name = "${var.project_name}-tg"
  }
}

# 4) Application Load Balancer
resource "aws_lb" "web_alb" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.public.*.id

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# 5) Listener on port 80
resource "aws_lb_listener" "web_listener" {
  load_balancer_arn = aws_lb.web_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_tg.arn
  }
}

# 6) Auto Scaling Group
resource "aws_autoscaling_group" "web_asg" {
  name                 = "${var.project_name}-asg"
  max_size             = var.max_size
  min_size             = var.min_size
  desired_capacity     = var.desired_capacity
  vpc_zone_identifier  = aws_subnet.private.*.id

  launch_template {
    id      = aws_launch_template.web_lt.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.web_tg.arn]

  tag {
    key                 = "Name"
    value               = "${var.project_name}-instance"
    propagate_at_launch = true
  }
}
