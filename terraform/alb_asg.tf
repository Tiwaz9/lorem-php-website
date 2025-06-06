# 1) Latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  owners      = ["amazon"]
  most_recent = true
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# 2) Launch Template: install NGINX + PHP + Git, then clone from GitHub
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
    yum update -y

    # Enable NGINX and PHP 7.4
    amazon-linux-extras enable nginx1 php7.4
    yum clean metadata
    yum install -y nginx php-fpm git

    # Create webroot directory
    mkdir -p /var/www/lorem-app

    # Clone from GitHub into the 'public' subfolder
    cd /var/www/lorem-app
    git clone --branch ${var.github_repo_branch} ${var.github_repo_url} public

    # Configure NGINX to serve PHP from /var/www/lorem-app/public
    cat > /etc/nginx/conf.d/lorem.conf << 'NGINX_CONF'
    server {
        listen       80;
        server_name  _;
        root         /var/www/lorem-app/public;
        index        index.php index.html;

        location / {
            try_files $uri $uri/ =404;
        }

        location ~ \.php$ {
            fastcgi_pass   127.0.0.1:9000;
            fastcgi_index  index.php;
            fastcgi_param  SCRIPT_FILENAME  /var/www/lorem-app/public$fastcgi_script_name;
            include        fastcgi_params;
        }
    }
    NGINX_CONF

    # Start PHP-FPM and NGINX
    systemctl enable php-fpm
    systemctl start  php-fpm
    systemctl enable nginx
    systemctl start  nginx
  EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-web-server"
    }
  }
}

# 3) Target Group for ALB (port 80 → HTTP)
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

# 4) Application Load Balancer (in public subnets)
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

# 5) Listener on ALB port 80 → forward to target group
resource "aws_lb_listener" "web_listener" {
  load_balancer_arn = aws_lb.web_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_tg.arn
  }
}

# 6) Auto Scaling Group (in private subnets)
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
