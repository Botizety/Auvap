"""
Report Generator

Generates human-readable reports of penetration testing episodes:
- Episode summary (success, steps, hosts compromised)
- Action sequence with explanations
- Knowledge graph snapshots
- Manager-Worker coordination timeline
- Recommendations for improvement
"""

from typing import List, Dict, Any
from datetime import datetime
from loguru import logger


class ReportGenerator:
    """
    Generate comprehensive reports for AUVAP episodes
    
    Reports include:
    - Executive summary
    - Detailed action log with explanations
    - Manager decisions timeline
    - Performance metrics
    - Lessons learned / recommendations
    """
    
    def __init__(self):
        """Initialize report generator"""
        logger.info("ReportGenerator initialized")
    
    def generate_episode_report(
        self,
        episode_num: int,
        state_manager,
        manager_agent,
        worker_agent,
        reward_machine,
        trajectory: List[Dict[str, Any]]
    ) -> str:
        """
        Generate complete episode report
        
        Args:
            episode_num: Episode number
            state_manager: State manager with episode data
            manager_agent: Manager agent
            worker_agent: Worker agent
            reward_machine: Reward machine
            trajectory: List of (state, action, reward) tuples
        
        Returns:
            Formatted report string (Markdown)
        """
        report_lines = []
        
        # Header
        report_lines.append(f"# AUVAP Episode Report #{episode_num}")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Executive Summary
        report_lines.extend(self._generate_summary(state_manager, reward_machine))
        report_lines.append("")
        
        # Performance Metrics
        report_lines.extend(self._generate_metrics(state_manager, manager_agent, worker_agent))
        report_lines.append("")
        
        # Manager Decisions
        report_lines.extend(self._generate_manager_timeline(manager_agent))
        report_lines.append("")
        
        # Action Sequence
        report_lines.extend(self._generate_action_log(trajectory))
        report_lines.append("")
        
        # Phase Progression
        report_lines.extend(self._generate_phase_progression(reward_machine))
        report_lines.append("")
        
        # Network Map
        report_lines.extend(self._generate_network_map(state_manager))
        report_lines.append("")
        
        # Recommendations
        report_lines.extend(self._generate_recommendations(state_manager, trajectory))
        
        return "\n".join(report_lines)
    
    def _generate_summary(self, state_manager, reward_machine) -> List[str]:
        """Generate executive summary"""
        stats = state_manager.get_statistics()
        
        success = reward_machine.current_phase == reward_machine.PenetrationPhase.GOAL_ACHIEVED
        
        summary = [
            "## Executive Summary",
            "",
            f"**Status:** {'✅ SUCCESS' if success else '⏳ IN PROGRESS'}",
            f"**Total Steps:** {stats['total_steps']}",
            f"**Hosts Compromised:** {stats['hosts_owned']}/{stats['hosts_discovered']}",
            f"**Current Phase:** {stats['phase']}",
            f"**Total Reward:** {stats['total_reward']:.2f}",
        ]
        
        if stats.get('goal_progress') != "N/A":
            summary.append(f"**Goal Progress:** {stats['goal_progress']}")
        
        return summary
    
    def _generate_metrics(self, state_manager, manager_agent, worker_agent) -> List[str]:
        """Generate performance metrics"""
        stats = state_manager.get_statistics()
        
        success_rate = 0
        if stats['successful_actions'] + stats['failed_actions'] > 0:
            success_rate = stats['successful_actions'] / (stats['successful_actions'] + stats['failed_actions'])
        
        metrics = [
            "## Performance Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Success Rate | {success_rate:.1%} |",
            f"| Actions Taken | {stats['total_steps']} |",
            f"| Successful Actions | {stats['successful_actions']} |",
            f"| Failed Actions | {stats['failed_actions']} |",
            f"| Services Discovered | {stats['services_found']} |",
            f"| Vulnerabilities Found | {stats['vulnerabilities_found']} |",
            f"| Credentials Found | {stats['credentials_found']} |",
            f"| Total Cost | {stats['total_cost']:.2f} |",
        ]
        
        return metrics
    
    def _generate_manager_timeline(self, manager_agent) -> List[str]:
        """Generate Manager decisions timeline"""
        timeline = [
            "## Manager Decisions Timeline",
            "",
        ]
        
        if not manager_agent.decision_history:
            timeline.append("*No Manager decisions recorded*")
            return timeline
        
        for i, decision in enumerate(manager_agent.decision_history, 1):
            timeline.append(f"### Decision {i}: {decision.subgoal.value}")
            timeline.append(f"- **Target:** {decision.target_host or 'N/A'}")
            timeline.append(f"- **Budget:** {decision.budget} actions")
            timeline.append(f"- **Stop Condition:** {decision.stop_condition}")
            timeline.append("")
        
        # Manager statistics
        stats = manager_agent.get_statistics()
        timeline.append("### Manager Statistics")
        timeline.append(f"- **Total Decisions:** {stats['total_decisions']}")
        timeline.append("- **Sub-goal Distribution:**")
        for sg, count in stats['subgoal_distribution'].items():
            timeline.append(f"  - {sg}: {count}")
        timeline.append("- **Success Rates:**")
        for sg, rate in stats['subgoal_success_rates'].items():
            timeline.append(f"  - {sg}: {rate:.1%}")
        
        return timeline
    
    def _generate_action_log(self, trajectory: List[Dict[str, Any]]) -> List[str]:
        """Generate detailed action log"""
        log = [
            "## Action Log",
            "",
            "*Showing last 20 actions*",
            "",
        ]
        
        recent_actions = trajectory[-20:] if len(trajectory) > 20 else trajectory
        
        for i, step in enumerate(recent_actions, 1):
            action = step.get('action', {})
            reward = step.get('reward', 0)
            
            log.append(f"**{i}.** {action.get('type', 'unknown')} - {action.get('tool', 'unknown')}")
            log.append(f"   - Target: {action.get('target', 'N/A')}")
            log.append(f"   - Reward: {reward:.2f}")
            log.append("")
        
        return log
    
    def _generate_phase_progression(self, reward_machine) -> List[str]:
        """Generate phase progression diagram"""
        phases = [
            "## Phase Progression",
            "",
            "```",
        ]
        
        phase_history = reward_machine.phase_history
        
        for i, phase in enumerate(phase_history):
            arrow = " → " if i < len(phase_history) - 1 else ""
            phases.append(f"{phase.value}{arrow}")
        
        phases.append("```")
        phases.append("")
        phases.append(f"**Current Phase:** {reward_machine.current_phase.value}")
        phases.append(f"**Progress:** {reward_machine.get_phase_progress():.1%}")
        
        return phases
    
    def _generate_network_map(self, state_manager) -> List[str]:
        """Generate network topology map"""
        network = [
            "## Network Topology",
            "",
            "```",
        ]
        
        # Show discovered hosts with ownership status
        for host_id, host in state_manager.hosts.items():
            if host.discovered:
                status = "🔴 OWNED" if host.owned else "🟡 DISCOVERED"
                priv = f"({host.privilege_level})" if host.owned else ""
                network.append(f"{status} {host_id} {priv}")
                
                # Show services
                if host.services:
                    for service in host.services:
                        network.append(f"  └─ {service}")
        
        network.append("```")
        
        # Connectivity matrix
        if state_manager.connectivity_matrix:
            network.append("")
            network.append("### Network Connections")
            for source, targets in state_manager.connectivity_matrix.items():
                for target in targets:
                    network.append(f"- {source} → {target}")
        
        return network
    
    def _generate_recommendations(self, state_manager, trajectory: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = [
            "## Recommendations",
            "",
        ]
        
        stats = state_manager.get_statistics()
        
        # Analyze performance and suggest improvements
        if stats['failed_actions'] > stats['successful_actions']:
            recommendations.append("⚠️ **High failure rate detected**")
            recommendations.append("   - Consider improving action masking")
            recommendations.append("   - Review precondition checks")
            recommendations.append("")
        
        if stats['hosts_owned'] < stats['hosts_discovered'] / 2:
            recommendations.append("⚠️ **Low exploitation rate**")
            recommendations.append("   - Focus more on exploitation phase")
            recommendations.append("   - Review vulnerability prioritization")
            recommendations.append("")
        
        if len(trajectory) > 100:
            recommendations.append("⚠️ **Long episode duration**")
            recommendations.append("   - Optimize action selection")
            recommendations.append("   - Improve goal-directed behavior")
            recommendations.append("")
        
        if not recommendations[2:]:  # Only header
            recommendations.append("✅ **Performance looks good!**")
            recommendations.append("   - Continue with current strategy")
        
        return recommendations
    
    def save_report(self, report: str, filename: str):
        """
        Save report to file
        
        Args:
            report: Report content
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")


if __name__ == "__main__":
    # Test report generator
    from ..environment.state_manager import StateManager
    from ..agents.manager import ManagerAgent
    from ..agents.worker import WorkerAgent
    from ..rewards.reward_machines import RewardMachine
    
    logger.info("Testing ReportGenerator...")
    
    # Create mock components
    state = StateManager()
    state.add_host("client", value=10)
    state.mark_owned("client", privilege="admin")
    state.add_host("web-01", value=50)
    state.mark_discovered("web-01")
    state.current_step = 25
    
    manager = ManagerAgent()
    worker = WorkerAgent(cbs_obs_dim=50)
    rm = RewardMachine()
    
    # Mock trajectory
    trajectory = [
        {'action': {'type': 'local', 'tool': 'scan'}, 'reward': 1.0},
        {'action': {'type': 'remote', 'tool': 'nmap', 'target': 'web-01'}, 'reward': 2.0},
        {'action': {'type': 'remote', 'tool': 'exploit', 'target': 'web-01'}, 'reward': 10.0},
    ]
    
    # Generate report
    generator = ReportGenerator()
    report = generator.generate_episode_report(
        episode_num=42,
        state_manager=state,
        manager_agent=manager,
        worker_agent=worker,
        reward_machine=rm,
        trajectory=trajectory
    )
    
    print(report)
    
    # Save report
    generator.save_report(report, "test_report.md")
    
    logger.info("Test completed!")
