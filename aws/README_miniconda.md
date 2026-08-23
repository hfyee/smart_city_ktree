sudo yum update -y
sudo yum install -y wget bzip2
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda
~/miniconda/bin/conda init bash
source ~/.bashrc
conda --version (result: conda 26.5.3)
rm ~/miniconda.sh

conda create -n ITG204 python=3.12.13 -y
conda activate ITG204
