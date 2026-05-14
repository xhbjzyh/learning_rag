"""
检查嵌入模型是否完整下载
运行方式：python scripts/check_model.py
"""
import os
from pathlib import Path


def check_model(model_path: str):
    """检查模型文件是否完整"""
    model_dir = Path(model_path)
    
    print(f"🔍 检查模型目录: {model_dir}")
    print("=" * 60)
    
    # 检查目录是否存在
    if not model_dir.exists():
        print(f"❌ 模型目录不存在: {model_path}")
        return False
    
    if not model_dir.is_dir():
        print(f"❌ 路径不是目录: {model_path}")
        return False
    
    # 列出所有文件
    files = list(model_dir.rglob("*"))
    files = [f for f in files if f.is_file()]
    
    print(f"📁 找到 {len(files)} 个文件\n")
    
    # 必需的核心文件
    required_files = [
        "config.json",
        "tokenizer.json",
        "vocab.txt",
    ]
    
    # 模型权重文件（可能有多种格式）
    weight_files = [
        "pytorch_model.bin",
        "model.safetensors",
        "tf_model.h5",
    ]
    
    has_weight = False
    missing_files = []
    
    # 检查每个文件
    print("📋 文件清单:")
    print("-" * 60)
    
    for file in sorted(files):
        rel_path = str(file.relative_to(model_dir))  # 🔥 修复：转换为字符串
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  ✓ {rel_path:<40} {size_mb:>8.2f} MB")
        
        # 检查是否是权重文件
        if file.name in weight_files and file.stat().st_size > 0:
            has_weight = True
    
    print("-" * 60)
    
    # 检查必需文件
    print("\n🔎 检查必需文件:")
    all_present = True
    
    for req_file in required_files:
        file_path = model_dir / req_file
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {req_file:<30} ({size_mb:.2f} MB)")
        else:
            print(f"  ❌ {req_file:<30} 缺失")
            missing_files.append(req_file)
            all_present = False
    
    # 检查权重文件
    print("\n🔎 检查模型权重:")
    if has_weight:
        for wf in weight_files:
            file_path = model_dir / wf
            if file_path.exists() and file_path.stat().st_size > 0:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ {wf:<30} ({size_mb:.2f} MB)")
                break
    else:
        print(f"  ❌ 未找到有效的模型权重文件")
        all_present = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_present and not missing_files:
        print("✅ 模型文件完整，可以正常使用！")
        # 🔥 修复：使用字符串拼接而非f-string中的replace
        config_line = "   EMBEDDING_MODEL_NAME=" + model_path.replace('\\', '/')
        print(f"\n💡 在 .env 文件中配置:")
        print(config_line)
        return True
    else:
        print("❌ 模型文件不完整！")
        if missing_files:
            print(f"\n缺失的文件:")
            for mf in missing_files:
                print(f"   - {mf}")
        print(f"\n💡 建议重新下载模型:")
        download_cmd = "   hf download BAAI/bge-small-zh-v1.5 --local-dir " + model_path.replace('\\', '/')
        print(download_cmd)
        return False


if __name__ == "__main__":
    # 默认检查路径
    default_path = r"D:\models\bge-small-zh-v1.5"
    
    import sys
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = default_path
    
    check_model(model_path)
