#!/usr/bin/env python3
"""
Module Grid Generator
명암 차이로 형상을 만드는 그래픽 패턴 생성기
"""

from PIL import Image
import numpy as np
import os
from pathlib import Path


class ModuleGridGenerator:
    def __init__(self, module_folder, target_image, grid_size=None, output_dpi=300):
        """
        Args:
            module_folder: 모듈 이미지들이 있는 폴더 경로
            target_image: 형상으로 만들 이미지 경로
            grid_size: (cols, rows) 튜플. None이면 자동 계산
            output_dpi: 출력 해상도 (기본 300)
        """
        self.module_folder = module_folder
        self.target_image = target_image
        self.grid_size = grid_size
        self.output_dpi = output_dpi
        self.modules = []
        self.module_brightness = []
        self.module_names = []  # 모듈 파일명 저장
        self.module_usage_count = {}  # 모듈 사용 횟수 카운트

    def analyze_modules(self):
        """모듈 이미지들의 평균 밝기 분석"""
        print("📊 모듈 분석 중...")

        # PNG, JPG 파일 모두 지원
        module_files = list(Path(self.module_folder).glob('*.png'))
        module_files.extend(Path(self.module_folder).glob('*.jpg'))
        module_files.extend(Path(self.module_folder).glob('*.jpeg'))
        module_files = sorted(module_files)

        if not module_files:
            raise FileNotFoundError(f"모듈 폴더에서 이미지를 찾을 수 없습니다: {self.module_folder}")

        for module_file in module_files:
            img = Image.open(module_file).convert('L')  # 그레이스케일 변환
            brightness = np.array(img).mean()  # 평균 밝기 (0=검정, 255=흰색)

            self.modules.append(img)
            self.module_brightness.append(brightness)
            self.module_names.append(module_file.name)
            self.module_usage_count[module_file.name] = 0  # 사용 횟수 초기화
            print(f"  {module_file.name}: 밝기 {brightness:.1f}")

        # 밝기 순으로 정렬 (어두운 것 -> 밝은 것)
        sorted_indices = np.argsort(self.module_brightness)
        self.modules = [self.modules[i] for i in sorted_indices]
        self.module_brightness = [self.module_brightness[i] for i in sorted_indices]
        self.module_names = [self.module_names[i] for i in sorted_indices]

        print(f"✅ {len(self.modules)}개 모듈 분석 완료")
        print(f"   밝기 범위: {self.module_brightness[0]:.1f} (어두움) ~ {self.module_brightness[-1]:.1f} (밝음)\n")
        return self

    def prepare_target_image(self):
        """타겟 이미지를 그리드로 변환"""
        print("🖼️  타겟 이미지 분석 중...")

        if not os.path.exists(self.target_image):
            raise FileNotFoundError(f"타겟 이미지를 찾을 수 없습니다: {self.target_image}")

        target = Image.open(self.target_image).convert('L')
        print(f"  원본 크기: {target.width} x {target.height} 픽셀")

        # 그리드 크기 자동 계산 (미지정 시)
        if self.grid_size is None:
            # 모듈이 최소 50x50 픽셀 정도 되도록
            module_size = self.modules[0].size[0]
            target_module_size = max(50, module_size // 2)
            cols = max(10, target.width // target_module_size)
            rows = max(10, target.height // target_module_size)
            self.grid_size = (cols, rows)
            print(f"  자동 계산된 그리드: {cols} x {rows}")
        else:
            cols, rows = self.grid_size
            print(f"  지정된 그리드: {cols} x {rows}")

        # 타겟 이미지를 그리드 크기로 리사이즈
        resized = target.resize((cols, rows), Image.Resampling.LANCZOS)
        self.grid_brightness = np.array(resized)

        print(f"✅ 이미지 그리드 변환 완료\n")
        return self

    def match_module(self, brightness):
        """밝기 값에 가장 가까운 모듈 선택"""
        distances = [abs(brightness - mb) for mb in self.module_brightness]
        best_index = np.argmin(distances)

        # 사용 횟수 증가
        module_name = self.module_names[best_index]
        self.module_usage_count[module_name] += 1

        return self.modules[best_index]

    def generate(self, output_path='output.png', invert=False, md_folder=None):
        """
        최종 이미지 생성

        Args:
            output_path: 출력 파일 경로
            invert: True면 명암 반전 (밝은 곳에 어두운 모듈)
            md_folder: 마크다운 파일을 저장할 폴더 (None이면 이미지와 같은 폴더)
        """
        print("🎨 최종 이미지 생성 중...")

        # 사용 횟수 초기화
        for name in self.module_usage_count:
            self.module_usage_count[name] = 0

        cols, rows = self.grid_size
        module_size = self.modules[0].size[0]  # 모든 모듈이 같은 크기라고 가정

        # 최종 캔버스 생성
        final_width = cols * module_size
        final_height = rows * module_size
        final_image = Image.new('RGB', (final_width, final_height), 'white')

        print(f"  최종 크기: {final_width} x {final_height} 픽셀")
        print(f"  모듈 크기: {module_size} x {module_size} 픽셀")

        # 각 그리드 셀에 모듈 배치
        for row in range(rows):
            for col in range(cols):
                brightness = self.grid_brightness[row, col]

                # 반전 옵션 적용
                if invert:
                    brightness = 255 - brightness

                module = self.match_module(brightness)

                # 모듈을 RGB로 변환하여 붙이기
                module_rgb = module.convert('RGB')
                x = col * module_size
                y = row * module_size
                final_image.paste(module_rgb, (x, y))

            # 진행상황 표시
            if (row + 1) % 10 == 0 or row == rows - 1:
                progress = (row + 1) / rows * 100
                print(f"  진행: {progress:.1f}% ({row + 1}/{rows} 행)")

        # 저장
        final_image.save(output_path, dpi=(self.output_dpi, self.output_dpi))

        # 파일 크기 계산
        file_size = os.path.getsize(output_path) / (1024 * 1024)

        print(f"\n✅ 완료! 저장됨: {output_path}")
        print(f"   이미지 크기: {final_width} x {final_height} 픽셀")
        print(f"   DPI: {self.output_dpi}")
        print(f"   파일 크기: {file_size:.2f} MB")

        # 인쇄 크기 계산 (mm)
        width_mm = (final_width / self.output_dpi) * 25.4
        height_mm = (final_height / self.output_dpi) * 25.4
        print(f"   인쇄 크기: {width_mm:.1f} x {height_mm:.1f} mm ({self.output_dpi}dpi 기준)")

        # 모듈 사용 횟수를 마크다운 파일로 저장
        if md_folder:
            os.makedirs(md_folder, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            usage_file = os.path.join(md_folder, base_name + '_usage.md')
        else:
            usage_file = os.path.splitext(output_path)[0] + '_usage.md'

        self.save_usage_stats(usage_file, output_path)

        return final_image

    def save_usage_stats(self, usage_file, output_image_path, copy_images=False):
        """모듈 사용 통계를 마크다운 파일로 저장

        Args:
            usage_file: 저장할 마크다운 파일 경로
            output_image_path: 결과 이미지 경로
            copy_images: True면 이미지를 md 파일 옆에 복사 (다른 사람에게 전달 시)
        """
        output_dir = os.path.dirname(os.path.abspath(usage_file))

        # 이미지 복사 옵션이 활성화된 경우
        if copy_images:
            # 이미지를 저장할 서브폴더 생성
            images_subfolder = os.path.join(output_dir, 'images')
            os.makedirs(images_subfolder, exist_ok=True)

            # 결과 이미지 복사
            output_image_abs = os.path.abspath(output_image_path)
            result_image_name = os.path.basename(output_image_abs)
            result_image_copy = os.path.join(images_subfolder, result_image_name)
            if os.path.exists(output_image_abs):
                import shutil
                shutil.copy2(output_image_abs, result_image_copy)
            result_path = f"images/{result_image_name}"

            # 타겟 이미지 복사
            if self.target_image and os.path.exists(self.target_image):
                target_image_abs = os.path.abspath(self.target_image)
                target_image_name = os.path.basename(target_image_abs)
                target_image_copy = os.path.join(images_subfolder, target_image_name)
                import shutil
                shutil.copy2(target_image_abs, target_image_copy)
                target_path = f"images/{target_image_name}"
            else:
                target_path = None

            # 모듈 이미지 복사
            modules_subfolder = os.path.join(images_subfolder, 'modules')
            os.makedirs(modules_subfolder, exist_ok=True)
            module_dir = os.path.abspath(self.module_folder)
            for module_name in self.module_names:
                module_src = os.path.join(module_dir, module_name)
                module_dst = os.path.join(modules_subfolder, module_name)
                if os.path.exists(module_src):
                    import shutil
                    shutil.copy2(module_src, module_dst)

        else:
            # 상대 경로 사용
            output_image_abs = os.path.abspath(output_image_path)
            try:
                result_path = os.path.relpath(output_image_abs, output_dir)
            except ValueError:
                result_path = output_image_abs

            if self.target_image and os.path.exists(self.target_image):
                target_image_abs = os.path.abspath(self.target_image)
                try:
                    target_path = os.path.relpath(target_image_abs, output_dir)
                except ValueError:
                    target_path = target_image_abs
            else:
                target_path = None

        with open(usage_file, 'w', encoding='utf-8') as f:
            f.write("# 모듈 사용 통계\n\n")

            # 결과 이미지 표시
            f.write("## 결과 이미지\n\n")
            f.write(f"![결과 이미지]({result_path})\n\n")

            # 타겟 이미지 표시
            if target_path:
                f.write("## 원본 타겟 이미지\n\n")
                f.write(f"![타겟 이미지]({target_path})\n\n")

            f.write("---\n\n")

            # 총 사용 횟수
            total_count = sum(self.module_usage_count.values())
            f.write(f"- **총 사용된 모듈 개수**: {total_count}\n")
            f.write(f"- **서로 다른 모듈 종류**: {len(self.module_usage_count)}\n\n")

            f.write("---\n\n")
            f.write("## 모듈별 사용 횟수\n\n")

            # 사용 횟수 순으로 정렬하여 출력
            sorted_usage = sorted(self.module_usage_count.items(), key=lambda x: x[1], reverse=True)

            # 테이블 헤더
            f.write("| 모듈 이미지 | 파일명 | 사용 횟수 | 비율 |\n")
            f.write("|:---:|:---|---:|---:|\n")

            # 모듈 이미지 경로
            for module_name, count in sorted_usage:
                percentage = (count / total_count * 100) if total_count > 0 else 0

                if copy_images:
                    module_path = f"images/modules/{module_name}"
                else:
                    module_dir = os.path.abspath(self.module_folder)
                    module_full_path = os.path.join(module_dir, module_name)
                    try:
                        module_path = os.path.relpath(module_full_path, output_dir)
                    except ValueError:
                        module_path = module_full_path

                f.write(f"| ![{module_name}]({module_path}) | {module_name} | {count} | {percentage:.2f}% |\n")

        print(f"📊 사용 통계 저장됨: {usage_file}")


def process_folder(module_folder, target_folder, output_folder, grid_size=None, output_dpi=300, invert=False, md_folder=None, copy_images=False):
    """
    폴더 내 모든 이미지를 일괄 처리

    Args:
        module_folder: 모듈 이미지 폴더
        target_folder: 타겟 이미지들이 있는 폴더
        output_folder: 결과물을 저장할 폴더
        grid_size: 그리드 크기
        output_dpi: 출력 DPI
        invert: 명암 반전 여부
        md_folder: 마크다운 파일을 저장할 폴더 (None이면 output_folder/md)
        copy_images: True면 이미지를 md 폴더에 복사 (전달용)
    """
    from pathlib import Path

    # 출력 폴더 생성
    os.makedirs(output_folder, exist_ok=True)

    # 지원하는 이미지 확장자
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']

    # 타겟 폴더에서 이미지 파일 찾기
    target_files = []
    for ext in image_extensions:
        target_files.extend(Path(target_folder).glob(f'*{ext}'))
        target_files.extend(Path(target_folder).glob(f'*{ext.upper()}'))

    target_files = sorted(set(target_files))

    if not target_files:
        print(f"❌ 타겟 폴더에서 이미지를 찾을 수 없습니다: {target_folder}")
        return

    print("=" * 60)
    print(f"📁 폴더 일괄 처리 시작")
    print("=" * 60)
    print(f"타겟 폴더: {target_folder}")
    print(f"출력 폴더: {output_folder}")
    print(f"찾은 이미지: {len(target_files)}개")
    print()

    # MD 파일 저장 폴더 설정
    if md_folder is None:
        md_folder = os.path.join(output_folder, 'md')
    os.makedirs(md_folder, exist_ok=True)

    # 생성기 초기화 (모듈 분석은 한 번만)
    generator = ModuleGridGenerator(
        module_folder=module_folder,
        target_image=str(target_files[0]),  # 임시로 첫 번째 이미지 사용
        grid_size=grid_size,
        output_dpi=output_dpi
    )
    generator.analyze_modules()

    # 전체 파일의 모듈 사용 통계 합산
    total_usage_count = {name: 0 for name in generator.module_names}
    processed_files = []

    # 각 이미지 처리
    success_count = 0
    fail_count = 0

    for idx, target_file in enumerate(target_files, 1):
        try:
            print(f"\n[{idx}/{len(target_files)}] 처리 중: {target_file.name}")
            print("-" * 60)

            # 타겟 이미지 업데이트
            generator.target_image = str(target_file)
            generator.prepare_target_image()

            # 출력 파일명 생성
            output_filename = f"{target_file.stem}_grid{target_file.suffix}"
            output_path = os.path.join(output_folder, output_filename)

            # 생성
            generator.generate(output_path, invert=invert, md_folder=md_folder)

            # copy_images 옵션 적용 (개별 MD 파일에)
            if copy_images:
                # MD 파일 경로 계산
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                individual_md = os.path.join(md_folder, base_name + '_usage.md')
                # 이미지 복사하여 재생성
                generator.save_usage_stats(individual_md, output_path, copy_images=True)

            success_count += 1

            # 전체 통계에 합산
            for module_name, count in generator.module_usage_count.items():
                total_usage_count[module_name] += count

            # 처리된 파일 정보 저장 (MD 파일 경로 포함)
            base_name = os.path.splitext(output_filename)[0]
            processed_files.append({
                'name': target_file.name,
                'output': output_filename,
                'output_path': output_path,
                'md_file': base_name + '_usage.md',
                'usage_count': dict(generator.module_usage_count)
            })

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            fail_count += 1
            continue

    # 전체 통계 저장
    if success_count > 0:
        total_md_path = os.path.join(md_folder, 'total.md')
        save_total_stats(total_md_path, total_usage_count, processed_files,
                        module_folder, generator.module_names, copy_images)

    # 최종 결과
    print("\n" + "=" * 60)
    print("📊 일괄 처리 완료")
    print("=" * 60)
    print(f"성공: {success_count}개")
    print(f"실패: {fail_count}개")
    print(f"출력 폴더: {output_folder}")
    print()


def save_total_stats(total_md_path, total_usage_count, processed_files, module_folder, module_names, copy_images=False):
    """전체 파일의 모듈 사용 통계를 저장"""
    output_dir = os.path.dirname(os.path.abspath(total_md_path))

    # 이미지 복사 옵션 처리
    if copy_images:
        # 모듈 이미지 복사
        modules_subfolder = os.path.join(output_dir, 'images', 'modules')
        os.makedirs(modules_subfolder, exist_ok=True)
        module_dir = os.path.abspath(module_folder)
        import shutil
        for module_name in module_names:
            module_src = os.path.join(module_dir, module_name)
            module_dst = os.path.join(modules_subfolder, module_name)
            if os.path.exists(module_src):
                shutil.copy2(module_src, module_dst)

        # 결과 이미지들 복사
        results_subfolder = os.path.join(output_dir, 'images', 'results')
        os.makedirs(results_subfolder, exist_ok=True)
        for file_info in processed_files:
            if 'output_path' in file_info and os.path.exists(file_info['output_path']):
                result_name = os.path.basename(file_info['output_path'])
                shutil.copy2(file_info['output_path'], os.path.join(results_subfolder, result_name))

    with open(total_md_path, 'w', encoding='utf-8') as f:
        f.write("# 전체 모듈 사용 통계\n\n")

        # 처리된 파일 목록 (링크 포함)
        f.write(f"## 처리된 파일 ({len(processed_files)}개)\n\n")
        for idx, file_info in enumerate(processed_files, 1):
            md_link = file_info.get('md_file', '')
            f.write(f"{idx}. {file_info['name']} → {file_info['output']} ([상세보기]({md_link}))\n")
        f.write("\n---\n\n")

        # 전체 사용 통계
        total_count = sum(total_usage_count.values())
        f.write(f"- **총 사용된 모듈 개수**: {total_count:,}\n")
        f.write(f"- **서로 다른 모듈 종류**: {len(total_usage_count)}\n")
        f.write(f"- **처리된 이미지 수**: {len(processed_files)}\n\n")

        f.write("---\n\n")
        f.write("## 모듈별 전체 사용 횟수\n\n")

        # 사용 횟수 순으로 정렬
        sorted_usage = sorted(total_usage_count.items(), key=lambda x: x[1], reverse=True)

        # 테이블 헤더
        f.write("| 모듈 이미지 | 파일명 | 전체 사용 횟수 | 비율 |\n")
        f.write("|:---:|:---|---:|---:|\n")

        # 모듈 이미지 경로
        module_dir = os.path.abspath(module_folder)
        for module_name, count in sorted_usage:
            percentage = (count / total_count * 100) if total_count > 0 else 0

            if copy_images:
                module_path = f"images/modules/{module_name}"
            else:
                module_full_path = os.path.join(module_dir, module_name)
                try:
                    module_path = os.path.relpath(module_full_path, output_dir)
                except ValueError:
                    module_path = module_full_path

            f.write(f"| ![{module_name}]({module_path}) | {module_name} | {count:,} | {percentage:.2f}% |\n")

        # 개별 파일 상세 통계
        f.write("\n---\n\n")
        f.write("## 개별 파일 상세 통계\n\n")

        for idx, file_info in enumerate(processed_files, 1):
            f.write(f"### {idx}. {file_info['name']}\n\n")

            # 결과 이미지
            if copy_images and 'output' in file_info:
                result_image_path = f"images/results/{file_info['output']}"
            elif 'output_path' in file_info:
                try:
                    result_image_path = os.path.relpath(file_info['output_path'], output_dir)
                except ValueError:
                    result_image_path = file_info['output_path']
            else:
                result_image_path = None

            if result_image_path:
                f.write(f"![{file_info['output']}]({result_image_path})\n\n")

            # 개별 파일의 모듈 사용 통계
            if 'usage_count' in file_info:
                individual_total = sum(file_info['usage_count'].values())
                f.write(f"**사용된 모듈 개수**: {individual_total:,}\n\n")

                # 상위 5개만 표시
                individual_sorted = sorted(file_info['usage_count'].items(), key=lambda x: x[1], reverse=True)
                f.write("**가장 많이 사용된 모듈 (Top 5)**:\n\n")
                for i, (mod_name, mod_count) in enumerate(individual_sorted[:5], 1):
                    mod_percentage = (mod_count / individual_total * 100) if individual_total > 0 else 0
                    f.write(f"{i}. {mod_name}: {mod_count}개 ({mod_percentage:.2f}%)\n")

            f.write(f"\n[전체 상세 통계 보기]({file_info.get('md_file', '')})\n\n")
            f.write("---\n\n")

    print(f"📊 전체 통계 저장됨: {total_md_path}")


def main():
    """사용 예시"""
    import argparse

    parser = argparse.ArgumentParser(description='모듈 그리드 생성기')
    parser.add_argument('--modules', '-m', required=True, help='모듈 이미지 폴더 경로')
    parser.add_argument('--target', '-t', help='타겟 이미지 경로 또는 폴더 경로')
    parser.add_argument('--target-folder', '-tf', help='타겟 이미지 폴더 경로 (일괄 처리)')
    parser.add_argument('--output', '-o', default='output.png', help='출력 파일 경로')
    parser.add_argument('--output-folder', '-of', help='출력 폴더 경로 (일괄 처리용)')
    parser.add_argument('--grid', '-g', help='그리드 크기 (예: 50x70)', default=None)
    parser.add_argument('--dpi', '-d', type=int, default=300, help='출력 DPI (기본: 300)')
    parser.add_argument('--invert', '-i', action='store_true', help='명암 반전')

    args = parser.parse_args()

    # 폴더 일괄 처리 모드
    if args.target_folder or args.output_folder:
        if not args.target_folder:
            print("❌ 오류: --target-folder (-tf) 옵션이 필요합니다.")
            return

        output_folder = args.output_folder or './output_folder'

        # 그리드 크기 파싱
        grid_size = None
        if args.grid:
            try:
                cols, rows = map(int, args.grid.split('x'))
                grid_size = (cols, rows)
            except:
                print(f"⚠️  잘못된 그리드 형식: {args.grid}. 자동 계산됩니다.")

        process_folder(
            module_folder=args.modules,
            target_folder=args.target_folder,
            output_folder=output_folder,
            grid_size=grid_size,
            output_dpi=args.dpi,
            invert=args.invert
        )
        return

    # 단일 이미지 처리 모드
    if not args.target:
        print("❌ 오류: --target (-t) 또는 --target-folder (-tf) 옵션이 필요합니다.")
        return

    # 그리드 크기 파싱
    grid_size = None
    if args.grid:
        try:
            cols, rows = map(int, args.grid.split('x'))
            grid_size = (cols, rows)
        except:
            print(f"⚠️  잘못된 그리드 형식: {args.grid}. 자동 계산됩니다.")

    # 생성기 실행
    generator = ModuleGridGenerator(
        module_folder=args.modules,
        target_image=args.target,
        grid_size=grid_size,
        output_dpi=args.dpi
    )

    generator.analyze_modules()
    generator.prepare_target_image()
    generator.generate(args.output, invert=args.invert)


if __name__ == "__main__":
    # 간단한 사용 예시
    print("=" * 60)
    print("Module Grid Generator")
    print("=" * 60)
    print()

    # 명령행 인자가 있으면 그것 사용, 없으면 기본값
    import sys

    if len(sys.argv) > 1:
        main()
    else:
        print("📖 사용법:")
        print()
        print("단일 이미지 처리:")
        print("  python module_grid_generator.py \\")
        print("      --modules ./modules \\")
        print("      --target ./horse.jpg \\")
        print("      --output ./result.png \\")
        print("      --grid 50x70 \\")
        print("      --dpi 300")
        print()
        print("폴더 일괄 처리:")
        print("  python module_grid_generator.py \\")
        print("      --modules ./modules \\")
        print("      --target-folder ./images \\")
        print("      --output-folder ./results \\")
        print("      --grid 50x70 \\")
        print("      --dpi 300")
        print()
        print("간단한 사용:")
        print("  python module_grid_generator.py -m ./modules -t ./horse.jpg -o result.png")
        print("  python module_grid_generator.py -m ./modules -tf ./images -of ./results")
        print()
        print("옵션:")
        print("  --modules, -m      : 모듈 이미지 폴더 (필수)")
        print("  --target, -t       : 타겟 이미지 파일 (단일 처리)")
        print("  --target-folder, -tf : 타겟 이미지 폴더 (일괄 처리)")
        print("  --output, -o       : 출력 파일명 (기본: output.png)")
        print("  --output-folder, -of : 출력 폴더 (일괄 처리)")
        print("  --grid, -g         : 그리드 크기 (예: 50x70, 생략시 자동)")
        print("  --dpi, -d          : 출력 DPI (기본: 300)")
        print("  --invert, -i       : 명암 반전")
        print()