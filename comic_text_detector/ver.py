# 在当前环境检查
python -c "try: import torch; print(f'Torch version: {torch.__version__}'); except ImportError: print('Torch not installed')"

# 在其他环境检查
conda activate paddleocr
python -c "try: import torch; print(f'Torch version: {torch.__version__}'); except ImportError: print('Torch not installed')"
conda deactivate