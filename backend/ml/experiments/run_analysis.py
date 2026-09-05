import json
from pathlib import Path
from backend.ml.experiments.calibration import ThresholdCalibrator
from backend.ml.experiments.error_mining import HardPositiveMiner

def main():
    prod_pt = Path('models/detection/sonar_yolov8_fls_trained.pt')
    v3_yaml = Path('datasets/sonar_debris_v3/data.yaml')

    print("Running threshold calibration...")
    calibrator = ThresholdCalibrator(prod_pt, v3_yaml)
    calib_res = calibrator.generate_calibration_reports(
        output_json=Path('reports/model_optimization/threshold_calibration.json'),
        output_md=Path('reports/model_optimization/threshold_calibration.md')
    )
    print("Calibration complete!")

    print("Running hard positive and failure mining...")
    miner = HardPositiveMiner(prod_pt)
    mining_res = miner.mine_failures(dataset_root=Path('datasets/sonar_debris_v3'))
    with open('reports/model_optimization/hard_positive_mining.json', 'w', encoding='utf-8') as f:
        json.dump(mining_res, f, indent=2)
    print(f"Mining complete! Scanned: {mining_res['total_images_scanned']}, missed: {mining_res['missed_debris_count']}, low conf: {mining_res['low_confidence_count']}")

if __name__ == '__main__':
    main()
