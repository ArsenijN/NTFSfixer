#!/usr/bin/env python3
"""
Bad Block Range Processor for HDSentinel data
INVERTED LOGIC: Input is GOOD blocks, output is BAD blocks to avoid
Optimized for NTFSMARKBAD batch mode
"""

def parse_blocks(data: str) -> list[int]:
    """Extract block numbers from HDSentinel data"""
    blocks = []
    for line in data.strip().split('\n'):
        parts = line.split()
        if parts and parts[0].isdigit():
            blocks.append(int(parts[0]))
    return sorted(set(blocks))

def invert_blocks(good_blocks: list[int], total_blocks: int) -> list[int]:
    """Convert list of GOOD blocks to list of BAD blocks"""
    good_set = set(good_blocks)
    return [b for b in range(total_blocks) if b not in good_set]

def create_ranges(blocks: list[int]) -> list[str]:
    """Convert list of blocks to range notation (e.g., 0-2, 4-10)"""
    if not blocks:
        return []
    
    ranges = []
    start = end = blocks[0]
    
    for block in blocks[1:]:
        if block == end + 1:
            end = block
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = end = block
    
    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ranges

def block_to_sector(block: int, sectors_per_block: int) -> int:
    """Convert block number to physical sector number"""
    return block * sectors_per_block

def main():
    print("="*70)
    print("NTFSMARKBAD BAD BLOCK PROCESSOR")
    print("For HDSentinel surface scan results")
    print("="*70)
    print()
    print("This script converts HDSentinel GOOD blocks to BAD sectors")
    print("for NTFSMARKBAD batch mode.")
    print()
    
    # Get drive info
    print("DRIVE INFORMATION:")
    print("-" * 70)
    
    total_sectors_input = input("Enter total drive sectors (e.g., 1953525168): ").strip()
    if not total_sectors_input:
        print("ERROR: Total sectors required!")
        return
    total_sectors = int(total_sectors_input)
    
    total_blocks_input = input("Enter total HDSentinel blocks (e.g., 10000): ").strip()
    total_blocks = int(total_blocks_input) if total_blocks_input else 10000
    
    # Calculate sectors per block
    sectors_per_block = total_sectors // total_blocks
    
    print()
    print(f"Drive size: {total_sectors:,} sectors ({total_sectors * 512 / 1e9:.2f} GB)")
    print(f"HDSentinel blocks: {total_blocks:,}")
    print(f"Sectors per block: {sectors_per_block:,} ({sectors_per_block * 512 / 1024 / 1024:.2f} MB)")
    print()
    
    # Get good blocks data
    print("="*70)
    print("INPUT: Paste HDSentinel GOOD blocks data")
    print("="*70)
    print("Press Ctrl+Z then Enter (Windows) or Ctrl+D (Linux/Mac) when done")
    print()
    
    try:
        lines = []
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    data = '\n'.join(lines)
    
    # Parse GOOD blocks
    good_blocks = parse_blocks(data)
    
    if not good_blocks:
        print("ERROR: No valid blocks found in input!")
        return
    
    print(f"\n✓ Parsed {len(good_blocks)} GOOD blocks from input")
    
    # Invert to get BAD blocks
    bad_blocks = invert_blocks(good_blocks, total_blocks)
    
    print(f"✓ Calculated {len(bad_blocks)} BAD blocks to mark")
    print()
    
    if not bad_blocks:
        print("="*70)
        print("SUCCESS: No bad blocks found!")
        print("="*70)
        print("Your drive appears healthy in the scanned area.")
        return
    
    # Statistics
    print("="*70)
    print("STATISTICS")
    print("="*70)
    bad_sectors_count = len(bad_blocks) * sectors_per_block
    bad_space_mb = bad_sectors_count * 512 / 1024 / 1024
    bad_space_gb = bad_space_mb / 1024
    
    print(f"Bad blocks:  {len(bad_blocks):,}")
    print(f"Bad sectors: {bad_sectors_count:,}")
    print(f"Space lost:  {bad_space_mb:.2f} MB ({bad_space_gb:.2f} GB)")
    print(f"Usable:      {100 * (1 - len(bad_blocks)/total_blocks):.2f}% of drive")
    print()
    
    # Create block ranges for reference
    bad_ranges = create_ranges(bad_blocks)
    
    # Convert bad blocks to sector ranges for NTFSMARKBAD
    sector_ranges = []
    for block in bad_blocks:
        sector_start = block_to_sector(block, sectors_per_block)
        sector_end = block_to_sector(block + 1, sectors_per_block) - 1
        sector_ranges.append((sector_start, sector_end))
    
    # Save files
    print("="*70)
    print("GENERATING FILES")
    print("="*70)
    
    # 1. NTFSMARKBAD batch file (main output)
    with open('ntfsmarkbad_sectors.txt', 'w') as f:
        for start, end in sector_ranges:
            f.write(f"{start} {end}\n")
    print("✓ ntfsmarkbad_sectors.txt - Ready for NTFSMARKBAD /B")
    
    # 2. Human-readable block ranges
    with open('bad_block_ranges.txt', 'w') as f:
        f.write(f"Bad blocks: {', '.join(bad_ranges)}\n")
        f.write(f"\nTotal: {len(bad_blocks)} bad blocks\n")
    print("✓ bad_block_ranges.txt - Human-readable block ranges")
    
    # 3. Linux badblocks format (optional - can be huge!)
    print()
    create_ext4 = input("Create badblocks_ext4.txt for Linux? (can be 2GB+) [y/N]: ").strip().lower()
    if create_ext4 == 'y':
        print("Creating badblocks_ext4.txt (this may take a while)...")
        with open('badblocks_ext4.txt', 'w') as f:
            for start, end in sector_ranges:
                for sector in range(start, end + 1):
                    f.write(f"{sector}\n")
        print("✓ badblocks_ext4.txt - For Linux ext4 (mkfs.ext4 -l)")
    else:
        print("⊘ Skipped badblocks_ext4.txt (use ntfsmarkbad_sectors.txt on Linux if needed)")
    
    # 4. Batch script for Windows
    with open('mark_bad_sectors.bat', 'w') as f:
        f.write('@echo off\n')
        f.write('REM NTFSMARKBAD Batch Script\n')
        f.write('REM https://github.com/jamersonpro/ntfsmarkbad\n')
        f.write('echo.\n')
        f.write('echo ====================================================================\n')
        f.write('echo NTFSMARKBAD - Mark Bad Sectors on NTFS\n')
        f.write('echo ====================================================================\n')
        f.write('echo.\n')
        f.write(f'echo This will mark {len(bad_blocks)} bad blocks ({bad_space_gb:.2f} GB) as unusable\n')
        f.write('echo.\n')
        f.write('echo REQUIREMENTS:\n')
        f.write('echo   1. NTFSMARKBAD.EXE in same folder\n')
        f.write('echo   2. Drive must be formatted as NTFS\n')
        f.write('echo   3. Run as Administrator\n')
        f.write('echo.\n')
        f.write('set /p DRIVE="Enter drive letter (e.g., D): "\n')
        f.write('echo.\n')
        f.write('echo Checking if NTFSMARKBAD.EXE exists...\n')
        f.write('if not exist "NTFSMARKBAD.EXE" (\n')
        f.write('    echo ERROR: NTFSMARKBAD.EXE not found!\n')
        f.write('    echo Download from: https://github.com/jamersonpro/ntfsmarkbad/releases\n')
        f.write('    pause\n')
        f.write('    exit /b 1\n')
        f.write(')\n')
        f.write('echo.\n')
        f.write('echo ====================================================================\n')
        f.write('echo Step 1: Format drive (WARNING: Erases all data!)\n')
        f.write('echo ====================================================================\n')
        f.write('set /p CONFIRM="Format %DRIVE%: as NTFS? (yes/no): "\n')
        f.write('if /i not "%CONFIRM%"=="yes" (\n')
        f.write('    echo Skipping format. Make sure drive is already formatted as NTFS!\n')
        f.write('    goto skip_format\n')
        f.write(')\n')
        f.write('echo.\n')
        f.write('echo Formatting %DRIVE%: ...\n')
        f.write('format %DRIVE%: /FS:NTFS /Q /V:BadSectorDrive\n')
        f.write('if errorlevel 1 (\n')
        f.write('    echo ERROR: Format failed!\n')
        f.write('    pause\n')
        f.write('    exit /b 1\n')
        f.write(')\n')
        f.write(':skip_format\n')
        f.write('echo.\n')
        f.write('echo ====================================================================\n')
        f.write('echo Step 2: Mark bad sectors\n')
        f.write('echo ====================================================================\n')
        f.write('echo.\n')
        f.write(f'echo Marking {len(bad_blocks)} bad blocks...\n')
        f.write('echo This may take a few minutes...\n')
        f.write('echo.\n')
        f.write('NTFSMARKBAD.EXE %DRIVE%: /B ntfsmarkbad_sectors.txt\n')
        f.write('if errorlevel 1 (\n')
        f.write('    echo.\n')
        f.write('    echo ERROR: NTFSMARKBAD failed!\n')
        f.write('    echo Check the output above for details.\n')
        f.write('    pause\n')
        f.write('    exit /b 1\n')
        f.write(')\n')
        f.write('echo.\n')
        f.write('echo ====================================================================\n')
        f.write('echo Step 3: Verify file system\n')
        f.write('echo ====================================================================\n')
        f.write('echo.\n')
        f.write('echo Running CHKDSK to verify...\n')
        f.write('CHKDSK %DRIVE%: /F\n')
        f.write('echo.\n')
        f.write('echo ====================================================================\n')
        f.write('echo SUCCESS!\n')
        f.write('echo ====================================================================\n')
        f.write(f'echo Marked {len(bad_blocks)} bad blocks as unusable\n')
        f.write(f'echo Lost space: {bad_space_gb:.2f} GB\n')
        f.write('echo Your drive is now ready for use (games/cache/non-critical data)\n')
        f.write('echo.\n')
        f.write('pause\n')
    print("✓ mark_bad_sectors.bat - Automated Windows script")
    
    # 5. Info file
    with open('README.txt', 'w', encoding='utf-8') as f:
        f.write("NTFSMARKBAD Bad Sector Marking\n")
        f.write("="*70 + "\n\n")
        f.write(f"Drive:           {total_sectors:,} sectors ({total_sectors * 512 / 1e9:.2f} GB)\n")
        f.write(f"Bad blocks:      {len(bad_blocks):,}\n")
        f.write(f"Bad sectors:     {bad_sectors_count:,}\n")
        f.write(f"Space lost:      {bad_space_gb:.2f} GB\n")
        f.write(f"Usable space:    {100 * (1 - len(bad_blocks)/total_blocks):.2f}%\n")
        f.write("\n")
        f.write("QUICK START (Windows):\n")
        f.write("-" * 70 + "\n")
        f.write("1. Download NTFSMARKBAD.EXE:\n")
        f.write("   https://github.com/jamersonpro/ntfsmarkbad/releases\n")
        f.write("   (Get NTFSMARKBAD.EXE for 64-bit or NTFSMARKBAD32.EXE for 32-bit)\n")
        f.write("\n")
        f.write("2. Put NTFSMARKBAD.EXE in this folder\n")
        f.write("\n")
        f.write("3. Right-click mark_bad_sectors.bat -> Run as Administrator\n")
        f.write("\n")
        f.write("4. Follow the prompts\n")
        f.write("\n")
        f.write("MANUAL METHOD:\n")
        f.write("-" * 70 + "\n")
        f.write("1. FORMAT D: /FS:NTFS /Q\n")
        f.write("2. NTFSMARKBAD.EXE D: /B ntfsmarkbad_sectors.txt\n")
        f.write("3. CHKDSK D: /F\n")
        f.write("\n")
        f.write("LINUX (ext4):\n")
        f.write("-" * 70 + "\n")
        f.write("Option 1 (if you created badblocks_ext4.txt):\n")
        f.write("  mkfs.ext4 -l badblocks_ext4.txt /dev/sdX\n")
        f.write("\n")
        f.write("Option 2 (convert from range format - faster):\n")
        f.write("  # Create badblocks.txt from ntfsmarkbad_sectors.txt:\n")
        f.write("  awk '{for(i=$1;i<=$2;i++)print i}' ntfsmarkbad_sectors.txt > badblocks.txt\n")
        f.write("  mkfs.ext4 -l badblocks.txt /dev/sdX\n")
        f.write("\n")
        f.write("FILES:\n")
        f.write("-" * 70 + "\n")
        f.write("- ntfsmarkbad_sectors.txt : Input file for NTFSMARKBAD /B\n")
        f.write("- mark_bad_sectors.bat    : Automated Windows script\n")
        f.write("- bad_block_ranges.txt    : Human-readable ranges\n")
        f.write("- README.txt              : This file\n")
        if create_ext4 == 'y':
            f.write("- badblocks_ext4.txt      : For Linux ext4 (large file!)\n")
        f.write("\n")
        f.write("NOTES:\n")
        f.write("-" * 70 + "\n")
        f.write("- NTFSMARKBAD uses PHYSICAL sector numbers (whole disk)\n")
        f.write("- No partition offset needed!\n")
        f.write("- Only unused clusters are marked as bad\n")
        f.write("- Safe for drives with full G-list (no write attempts)\n")
        f.write("\n")
        f.write("For ST1000DM003 drives:\n")
        f.write("- This is perfect for games/cache (non-critical data)\n")
        f.write("- NTFS will avoid these sectors automatically\n")
        f.write("- No reallocation attempts = no SATA hangs\n")
    print("✓ README.txt - Instructions and info")
    
    print()
    print("="*70)
    print("DONE!")
    print("="*70)
    print()
    print("NEXT STEPS:")
    print("  1. Download NTFSMARKBAD.EXE from:")
    print("     https://github.com/jamersonpro/ntfsmarkbad/releases")
    print()
    print("  2. Run: mark_bad_sectors.bat (as Administrator)")
    print()
    print("     OR manually:")
    print("     FORMAT D: /FS:NTFS /Q")
    print("     NTFSMARKBAD.EXE D: /B ntfsmarkbad_sectors.txt")
    print("     CHKDSK D: /F")
    print()
    
    if len(bad_blocks) > 2000:
        print("⚠ WARNING: Over 2000 bad blocks detected!")
        print("  This drive is severely degraded.")
        print("  Recommend: Use only for truly expendable data.")
        print()
    elif len(bad_blocks) > 500:
        print("⚠ CAUTION: Over 500 bad blocks.")
        print("  Drive is deteriorating. Monitor closely.")
        print()

if __name__ == "__main__":
    main()