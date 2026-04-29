SCRIPT_DIR="research/eda-schema-v2/baseline_analysis"
mkdir -p $SCRIPT_DIR/results

pdks=("NG45" "SKY130" "IHP130" "ASAP7")
stages=("floorplan" "global_place" "detailed_place" "cts" "global_route")
stages=("global_route")
problems=(
  "cell_arc_slew_prediction"
  "cell_arc_delay_prediction"
  "net_arc_delay_prediction"
  "timing_path_slack_prediction"
  "timing_path_arrival_time_prediction"
  "interconnect_length_prediction"
  "total_negative_slack_prediction"
  "worst_slack_prediction"
  "worst_arrival_time_prediction"
  "total_wirelength_prediction"
  "total_power_prediction"
  "total_area_prediction"
)

echo "Starting baseline analysis..."

echo "Starting baseline analysis vs actual..."
for pdk in "${pdks[@]}"; do
  for stage in "${stages[@]}"; do
    for problem in "${problems[@]}"; do
      # ------------------------------
      # Skip invalid combinations
      # ------------------------------
      if [[ "$stage" == "floorplan" && \
            ( "$problem" == "total_wirelength_prediction" || \
              "$problem" == "interconnect_length_prediction" ) ]]; then
        continue
      fi

      echo "Processing PDK: $pdk, Stage: $stage, Problem: $problem"
      time=$(date +%Y%m%d_%H%M%S)
      /usr/bin/time -v python $SCRIPT_DIR/compute_baseline_vs_actual.py \
        --problem "$problem" \
        --pdk "$pdk" \
        --initial-stage "$stage" 2>> $SCRIPT_DIR/run_global_route.log | tee -a $SCRIPT_DIR/run_global_route.log
      echo "Finished PDK: $pdk, Stage: $stage, Problem: $problem, Time: $time"
    done
  done
done

echo "All baseline analyses vs actual completed."

echo "Computing error metrics..."
time=$(date +%Y%m%d_%H%M%S)
/usr/bin/time -v python $SCRIPT_DIR/compute_error_metrics.py 2>> $SCRIPT_DIR/run_global_route.log | tee -a $SCRIPT_DIR/run_global_route.log
echo "Finished error metrics, Time: $time"
echo "All error metrics completed."

echo "Plotting results..."
time=$(date +%Y%m%d_%H%M%S)
python $SCRIPT_DIR/plot.py 2>> $SCRIPT_DIR/run_global_route.log | tee -a $SCRIPT_DIR/run_global_route.log
echo "Finished plotting results, Time: $time"
echo "All plotting results completed."

echo "Cleaning results..."
rm -rf $SCRIPT_DIR/results/*
echo "Results cleaned."

echo "Baseline analyses completed."