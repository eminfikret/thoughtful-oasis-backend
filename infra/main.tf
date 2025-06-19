terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "http" {}
}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "vpc" {
  cidr_block           = var.vpc_cidr_block
  instance_tenancy     = "default"
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc-${var.node_env}"
  }
}

resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.public_subnet_1_cidr
  availability_zone       = var.availability_zone_1
  map_public_ip_on_launch = true
  tags                    = {
    Name = "${var.project_name}-public-subnet-1-${var.node_env}"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.vpc.id
  cidr_block              = var.public_subnet_2_cidr
  availability_zone       = var.availability_zone_2
  map_public_ip_on_launch = true
  tags                    = {
    Name = "${var.project_name}-public-subnet-2-${var.node_env}"
  }
}

resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = var.private_subnet_1_cidr
  availability_zone = var.availability_zone_1
  tags              = {
    Name = "${var.project_name}-private-subnet-1-${var.node_env}"
  }
}

resource "aws_subnet" "private_subnet_2" {
  vpc_id            = aws_vpc.vpc.id
  cidr_block        = var.private_subnet_2_cidr
  availability_zone = var.availability_zone_2
  tags              = {
    Name = "${var.project_name}-private-subnet-2-${var.node_env}"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags   = {
    Name = "${var.project_name}-igw-${var.node_env}"
  }
}

resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg-${var.node_env}"
  description = "Security group for load balancing"
  vpc_id      = aws_vpc.vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg-${var.node_env}"
  }
}

resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-ec2-sg-${var.node_env}"
  description = "Security group for EC2"
  vpc_id      = aws_vpc.vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ec2-sg-${var.node_env}"
  }
}

resource "aws_security_group" "rds_ec2_sg" {
  name        = "${var.project_name}-rds-ec2-sg-${var.node_env}"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-ec2-sg-${var.node_env}"
  }
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  route {
    cidr_block = var.vpc_cidr_block
    gateway_id = "local"
  }

  tags = {
    Name = "${var.project_name}-public-route-table-${var.node_env}"
  }
}

resource "aws_main_route_table_association" "main_route_table" {
  vpc_id         = aws_vpc.vpc.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "public_route_table_association_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "public_route_table_association_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = var.vpc_cidr_block
    gateway_id = "local"
  }

  tags = {
    Name = "${var.project_name}-private-route-table-${var.node_env}"
  }
}

resource "aws_route_table_association" "private_rt_association_1" {
  subnet_id      = aws_subnet.private_subnet_1.id
  route_table_id = aws_route_table.private_route_table.id
}

resource "aws_route_table_association" "private_rt_association_2" {
  subnet_id      = aws_subnet.private_subnet_2.id
  route_table_id = aws_route_table.private_route_table.id
}

resource "aws_autoscaling_group" "autoscaling-group" {
  name                      = "${var.project_name}-ags-${var.node_env}"
  max_size                  = 4
  desired_capacity          = 2
  min_size                  = 2
  health_check_grace_period = 300
  health_check_type         = "ELB"
  force_delete              = true
  vpc_zone_identifier       = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

  launch_template {
    id      = aws_launch_template.ec2_template.id
    version = aws_launch_template.ec2_template.latest_version
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup        = 300
    }
  }

  tag {
    key                 = "Name"
    propagate_at_launch = true
    value               = "${var.project_name}-ags-${var.node_env}"
  }

  depends_on = [aws_db_instance.postgres_db]
}

data "template_file" "ec2_template_user_data" {
  template = file("${path.module}/user_data.sh")
  vars     = {
    CI_DEPLOY_USER     = var.ci_deploy_user
    CI_DEPLOY_PASSWORD = var.ci_deploy_password
    CI_REGISTRY_IMAGE  = var.ci_registry_image
    CI_COMMIT_SHORT_SHA = var.ci_commit_short_sha
    CI_REGISTRY        = var.ci_registry
    NODE_ENV           = var.node_env
    DB_HOST     = aws_db_instance.postgres_db.address
    DB_NAME     = "${var.db_name}${var.node_env}"
    DB_USERNAME = var.db_user
    DB_PASSWORD = var.db_password
  }

  depends_on = [aws_db_instance.postgres_db]
}

resource "aws_launch_template" "ec2_template" {
  name                   = "${var.project_name}-ec2-template-${var.node_env}"
  description            = "Launch template for EC2"
  image_id               = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  update_default_version = true
  user_data              = base64encode(data.template_file.ec2_template_user_data.rendered)

  tag_specifications {
    resource_type = "instance"
    tags          = {
      Name = "${var.project_name}-ec2-${var.node_env}"
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    instance_metadata_tags      = "enabled"
    http_put_response_hop_limit = 2
  }

  depends_on = [aws_db_instance.postgres_db]
}

resource "aws_lb" "lb" {
  name               = "${var.node_env}"
  internal           = false
  load_balancer_type = "application"
  ip_address_type    = "ipv4"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

  tags = {
    Name = "${var.project_name}-lb-${var.node_env}"
  }
}

resource "aws_lb_listener" "alb_listener" {
  load_balancer_arn = aws_lb.lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lb_target_group.arn
  }
}

resource "aws_lb_target_group" "lb_target_group" {
  name        = "${var.project_name}-lb-tg-${var.node_env}"
  target_type = "instance"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.vpc.id

  tags = {
    Name = "${var.project_name}-lb-tg-${var.node_env}"
  }
}

resource "aws_autoscaling_attachment" "autoscaling_attachment" {
  autoscaling_group_name = aws_autoscaling_group.autoscaling-group.name
  lb_target_group_arn    = aws_lb_target_group.lb_target_group.arn
}

resource "aws_db_subnet_group" "db_private_subnet_group" {
  name       = "${var.project_name}-db-private-subnet-group-${var.node_env}"
  subnet_ids = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]

  tags = {
    Name = "${var.project_name}-db-private-subnet-group-${var.node_env}"
  }
}

resource "aws_db_instance" "postgres_db" {
  identifier             = "${var.db_name}-${var.node_env}"
  engine                 = "postgres"
  engine_version         = "14"
  instance_class         = "db.t3.micro"
  username               = var.db_user
  password               = var.db_password
  db_name                = "${var.db_name}${var.node_env}"
  allocated_storage      = 10
  storage_type           = "gp2"
  multi_az               = true
  skip_final_snapshot    = true
  publicly_accessible    = false

  vpc_security_group_ids = [aws_security_group.rds_ec2_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.db_private_subnet_group.name

  depends_on = [aws_db_subnet_group.db_private_subnet_group]
}