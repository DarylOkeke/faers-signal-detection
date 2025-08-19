#!/usr/bin/env python3
"""
Cardiac Endpoints: Case Counts (left) + PRR Forest Plot (right)

Changes vs your prior version:
- Panel titles positioned: A shifted left, B shifted right.
- Forest plot labels show PRR (formatted) on each marker (no N labels).
- Tighter visual spacing: reduced subplot wspace and smarter x-limits
  (caps extreme UCLs via 95th percentile so points cluster better).
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set professional styling
plt.style.use('default')
sns.set_palette("husl")

# Configure matplotlib for high-quality, professional output
plt.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.family': 'DejaVu Sans',
    'font.size': 12,
    'axes.labelsize': 13,
    'axes.titlesize': 15,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 12,
    'figure.titlesize': 17,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.8,
    'lines.linewidth': 3.0,
    'patch.linewidth': 1.0,
    'axes.linewidth': 1.5,
    'xtick.major.width': 1.5,
    'ytick.major.width': 1.5,
    'xtick.minor.width': 1.0,
    'ytick.minor.width': 1.0,
    'axes.edgecolor': '#333333',
    'text.color': '#333333',
    'axes.labelcolor': '#333333'
})

COHORT_ORDER = ['HYDRALAZINE', 'MINOXIDIL_SYSTEMIC', 'MINOXIDIL_TOPICAL']
REACTION_ORDER = ['CARDIAC TAMPONADE', 'PERICARDIAL EFFUSION', 'PERICARDITIS', 'PLEURAL EFFUSION']
COHORT_COLORS = {
    'HYDRALAZINE': '#D32F2F',          # Professional red
    'MINOXIDIL_SYSTEMIC': '#FF8C00',   # Professional orange  
    'MINOXIDIL_TOPICAL': '#2E7D32'     # Professional green
}

def _complete_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with a complete Reaction×Cohort grid, left-joined to df."""
    grid = (pd.MultiIndex.from_product([REACTION_ORDER, COHORT_ORDER],
                                       names=['reaction_pt', 'cohort'])
            .to_frame(index=False))
    df2 = df.copy()

    # Coerce expected columns to numeric (create if missing)
    for col in ['PRR', 'PRR_LCL', 'PRR_UCL', 'N']:
        if col not in df2.columns:
            df2[col] = np.nan
        df2[col] = pd.to_numeric(df2[col], errors='coerce')

    # Left-join
    out = grid.merge(
        df2[['cohort', 'reaction_pt', 'PRR', 'PRR_LCL', 'PRR_UCL', 'N']],
        on=['reaction_pt', 'cohort'], how='left'
    )

    # Fill missing with zeros for plotting
    out[['PRR', 'PRR_LCL', 'PRR_UCL', 'N']] = out[['PRR', 'PRR_LCL', 'PRR_UCL', 'N']].fillna(0.0)

    # Ordered categories for stable sort
    out['reaction_cat'] = pd.Categorical(out['reaction_pt'], categories=REACTION_ORDER, ordered=True)
    out['cohort_cat']   = pd.Categorical(out['cohort'],      categories=COHORT_ORDER,   ordered=True)
    out = out.sort_values(['reaction_cat', 'cohort_cat']).reset_index(drop=True)

    # Create tighter y positions with better reaction grouping
    y_positions = []
    current_y = 0
    within_group_spacing = 0.32  # Slightly increased to prevent overlap
    between_group_spacing = 1.2  # More space between different reactions
    
    for r in REACTION_ORDER:
        block = out[out['reaction_pt'] == r]
        if len(block) > 0:
            # Assign y positions for this reaction group
            for i, idx in enumerate(block.index):
                y_positions.append(current_y + i * within_group_spacing)
            current_y += (len(block) - 1) * within_group_spacing + between_group_spacing
    
    out['y'] = y_positions

    # Right y-axis short cohort labels
    out['cohort_short'] = out['cohort'].str.replace('MINOXIDIL_', 'MIN_', regex=False)

    # Centers of each reaction block for left y-axis labels
    centers = []
    current_y = 0
    within_group_spacing = 0.32  # Match the spacing used above
    for r in REACTION_ORDER:
        block = out[out['reaction_pt'] == r]
        if len(block) > 0:
            # Calculate center of this reaction group
            group_center = current_y + (len(block) - 1) * within_group_spacing / 2
            centers.append(group_center)
            current_y += (len(block) - 1) * within_group_spacing + between_group_spacing
    out.attrs['reaction_centers'] = centers
    return out

def create_combined_plot(
    df,
    output_path="results/figures/cardiac_combined_plot.png",
    title="Cardiac Endpoints: Case Counts and PRR Analysis",
    figsize=(16, 8),
    prr_label_fmt="{:.2f}",     # format for PRR labels
    center_label_on_marker=True # True = center label on marker; False = to the right
):
    """One combined figure (left=bar counts; right=PRR forest). Robust to missing rows."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plot_df = _complete_grid(df)

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=figsize, gridspec_kw={'width_ratios': [1, 1.6]}
    )

    # ===== Left panel: bar counts (N) with enhanced styling =====
    for _, row in plot_df.iterrows():
        n_value = int(row['N'])
        
        # Only show bars for non-zero values
        if n_value > 0:
            # Create thicker, more professional bars with no overlap
            bar = ax1.barh(
                row['y'], n_value, height=0.3,  # Reduced height to prevent overlap
                color=COHORT_COLORS.get(row['cohort'], 'black'),
                edgecolor='white', linewidth=1.2, alpha=0.85,  # Thicker edges, slight transparency
                capstyle='round'  # Rounded bar edges
            )
            
            # Add subtle gradient effect
            for patch in bar:
                patch.set_linewidth(1.2)
        
        # Enhanced N labels with better positioning and styling
        if n_value > 0:
            x_text = n_value + max(1, max(plot_df['N']) * 0.02)
        else:
            x_text = 0.5  # Position zero labels near the y-axis
        
        # Show actual N value in label
        ax1.text(x_text, row['y'], f"{n_value}",
                 va='center', ha='left', fontsize=10, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='none', alpha=0.8))

    # Enhanced left panel styling
    ax1.set_xlabel('Number of Cases (N)', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_title('A. Case Counts', fontsize=14, fontweight='bold', pad=15, x=0.08)
    ax1.set_yticks(plot_df.attrs['reaction_centers'])
    ax1.set_yticklabels(REACTION_ORDER, fontsize=11, fontweight='medium')
    ax1.set_ylim(-0.7, plot_df['y'].max() + 0.7)  # More spacing
    max_count = max(10, int(plot_df['N'].max()))
    ax1.set_xlim(0, max_count * 1.3)  # More space for labels
    ax1.grid(True, alpha=0.25, axis='x', linewidth=0.8)
    ax1.spines['left'].set_linewidth(1.5)
    ax1.spines['bottom'].set_linewidth(1.5)

    # ===== Right panel: Enhanced PRR forest plot =====
    plotted_cohorts = set()
    
    for _, row in plot_df.iterrows():
        y = row['y']
        prr = float(row['PRR'])
        lcl = float(row['PRR_LCL'])
        ucl = float(row['PRR_UCL'])
        cohort = row['cohort']

        # On log scale, avoid 0 and shift zeros away from reference line
        if prr == 0:
            prr_plot = 0.015  # Closer to 10^-2 line (0.01)
        else:
            prr_plot = max(prr, 0.01)
 
        # Error bars
        if prr == 0 or (lcl == 0 and ucl == 0):
            xerr = [[0.0], [0.0]]
        else:
            xerr = [[max(prr_plot - lcl, 0.0)], [max(ucl - prr_plot, 0.0)]]

        # Skip markers for MINOXIDIL_TOPICAL zero values but keep labels
        if not (cohort == 'MINOXIDIL_TOPICAL' and prr == 0):
            # Enhanced square markers with thicker lines and better styling
            ax2.errorbar(
                prr_plot, y, xerr=xerr,
                fmt='s',
                color=COHORT_COLORS.get(cohort, 'black'),
                markersize=9,  # Larger markers
                capsize=4,     # Larger caps
                capthick=2.0,  # Thicker caps
                linewidth=2.5, # Thicker error bars
                alpha=0.9,
                markeredgecolor='white',
                markeredgewidth=1.0,
                label=cohort if cohort not in plotted_cohorts else ""
            )
            plotted_cohorts.add(cohort)
        else:
            # Add MINOXIDIL_TOPICAL to legend even without marker
            if cohort not in plotted_cohorts:
                ax2.plot([], [], 's', color=COHORT_COLORS.get(cohort, 'black'), 
                        markersize=9, alpha=0.9, markeredgecolor='white',
                        markeredgewidth=1.0, label=cohort)
                plotted_cohorts.add(cohort)

        # Enhanced PRR value labels with better styling and positioning for zeros
        lbl = prr_label_fmt.format(prr) if prr > 0 else "0"
        if center_label_on_marker:
            # For zero values, position label slightly to the left to avoid overlap
            if prr == 0:
                ax2.annotate(
                    lbl, (prr_plot, y),
                    xytext=(-8, 0), textcoords='offset points',
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", 
                             edgecolor='lightgray', alpha=0.9, linewidth=0.8)
                )
            else:
                ax2.annotate(
                    lbl, (prr_plot, y),
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="white", 
                             edgecolor='lightgray', alpha=0.9, linewidth=0.8)
                )
        else:
            ax2.annotate(
                lbl, (prr_plot, y),
                xytext=(4, 0), textcoords='offset points',
                ha='left', va='center', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", 
                         edgecolor='lightgray', alpha=0.9, linewidth=0.8)
            )

    ax2.set_xscale('log', base=10)
    
    # Enhanced reference lines with better styling
    ax2.axvline(1, color='#333333', linestyle='--', linewidth=2.0, alpha=0.7, 
               label='No Effect (PRR=1)', zorder=1)
    ax2.axvline(2, color='#D32F2F', linestyle=':', linewidth=2.0, alpha=0.8, 
               label='Signal Threshold (PRR=2)', zorder=1)
    ax2.set_xlabel('Proportional Reporting Ratio (PRR)', fontsize=12, fontweight='bold', labelpad=10)
    ax2.set_title('B. PRR Forest Plot (95% CI)', fontsize=14, fontweight='bold', pad=15, x=0.92)
    ax2.set_yticks(plot_df['y'])
    ax2.set_yticklabels([''] * len(plot_df))  # blank; cohort labels on twin axis
    ax2.set_ylim(-0.7, plot_df['y'].max() + 0.7)  # Consistent spacing with left panel

    # Smarter xmax so extreme UCLs don’t blow out the scale
    valid_ucl = plot_df['PRR_UCL'].replace(0, np.nan)
    if valid_ucl.notna().any():
        xmax_auto = float(np.nanquantile(valid_ucl, 0.95) * 1.4)  # 95th pct + headroom
        xmax = max(10, min(1000, xmax_auto))  # guardrails
    else:
        xmax = 10
    ax2.set_xlim(0.01, xmax)
    ax2.grid(True, alpha=0.25, axis='x', linewidth=0.8)
    ax2.spines['left'].set_linewidth(1.5)
    ax2.spines['bottom'].set_linewidth(1.5)

    # Enhanced right y-axis with cohort labels
    ax2r = ax2.twinx()
    ax2r.set_yticks(plot_df['y'])
    ax2r.set_yticklabels(plot_df['cohort_short'], fontsize=10, fontweight='medium')
    ax2r.set_ylim(ax2.get_ylim())
    ax2r.set_ylabel('Drug Cohort', fontsize=12, fontweight='bold', labelpad=10)
    ax2r.spines['right'].set_linewidth(1.5)

    # Enhanced legend with better styling (minimized size)
    handles = []
    for cohort in plotted_cohorts:
        handles.append(plt.Rectangle((0, 0), 1, 1, color=COHORT_COLORS[cohort], 
                                   alpha=0.85, label=cohort))
    
    # Add reference lines to legend
    ref_handles = [
        plt.Line2D([0], [0], color='#333333', linestyle='--', linewidth=2.0, 
                   alpha=0.7, label='No effect (PRR=1)'),
        plt.Line2D([0], [0], color='#D32F2F', linestyle=':', linewidth=2.0, 
                   alpha=0.8, label='Signal threshold (PRR=2)')
    ]
    
    all_handles = handles + ref_handles
    ax2.legend(
        handles=all_handles, loc='upper right',
        frameon=True, fancybox=True, shadow=True, fontsize=9,  # Reduced from 10
        title='Drug Cohorts & Reference Lines', title_fontsize=9,  # Reduced from 11
        edgecolor='gray', facecolor='white', framealpha=0.95,
        borderpad=0.4, columnspacing=0.8, handlelength=1.2, handletextpad=0.4  # Compact spacing
    )

    # Enhanced overall layout and styling
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97, 
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.1))
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, wspace=0.20, left=0.08, right=0.95, bottom=0.10)

    # Save with enhanced quality
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', 
                edgecolor='none', transparent=False, pad_inches=0.2)
    print(f"✓ Enhanced combined plot saved to: {output_path}")
    return fig

def main():
    import argparse
    p = argparse.ArgumentParser(description="Generate combined bar + forest plots for cardiac endpoints")
    p.add_argument('--input', '-i', default='cardiac_complete.csv', help='Input CSV path')
    p.add_argument('--combined-output', '-c', default='results/figures/cardiac_combined_plot.png', help='Output PNG path')
    p.add_argument('--title', '-t', default='Cardiac Endpoints: Case Counts and PRR Analysis', help='Figure title')
    p.add_argument('--center-prr-labels', action='store_true', help='Center PRR labels on markers (default True)')
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: not found: {args.input}")
        return 1

    df = pd.read_csv(args.input)
    required = {'cohort','reaction_pt','PRR','PRR_LCL','PRR_UCL','N'}
    missing = required.difference(df.columns)
    if missing:
        print(f"Error: missing columns: {sorted(missing)}")
        return 1

    create_combined_plot(
        df,
        output_path=args.combined_output,
        title=args.title,
        center_label_on_marker=True  # you can flip to False if you want labels to the right
    )
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
