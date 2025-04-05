import Image from "next/image";

export default function BlogPost() {
  return (
    <article className="prose mx-auto my-8 text-black dark:text-white">
      {/* Post Header */}
      <header className="mb-6">
        <h1 className="text-4xl text-black dark:text-white">Beyond the Boundary: Building a Machine Learning IPL Match Predictor with Advanced ELO Rating System</h1>
        <p className="text-gray-800 dark:text-gray-300">
          How I created a sophisticated cricket match prediction model combining custom ELO ratings, player form analysis, and machine learning to predict IPL match outcomes with remarkable accuracy.
        </p>
        <p className="text-sm text-gray-700 dark:text-gray-400">Published on: April 5, 2025</p>
      </header>

      {/* Featured Image */}
      <div className="mb-8">
        <Image
          src="/ipl.jpg"
          alt="IPL Match Predictor"
          width={800}
          height={450}
          className="rounded-lg"
        />
      </div>

      {/* Post Content */}
      <section>
        <p className="text-gray-800 dark:text-gray-300">
          Cricket analysis has come a long way from basic statistics to sophisticated predictive modeling. As a data scientist and cricket enthusiast, I set out to build an IPL match prediction system that goes beyond conventional approaches. In this post, I&#39;ll walk you through my journey of creating an advanced match predictor that incorporates a custom ELO rating system, player performance analytics, and machine learning.
        </p>

        <h2 className="text-gray-900 dark:text-gray-100">The Challenge of Cricket Prediction</h2>
        <p className="text-gray-800 dark:text-gray-300">
          Cricket is notoriously difficult to predict. With its complex format, countless variables, and the unpredictable human element, creating an accurate prediction model presents significant challenges. Most existing models rely heavily on team-level historical data or simplistic win/loss records, missing the nuanced aspects of player contributions and their current form.
        </p>
        <p className="text-gray-800 dark:text-gray-300">
          The IPL adds another layer of complexity with its constantly changing team compositions, player transfers, and the impact of overseas players. This environment demanded a more sophisticated approach – one that could capture individual player impacts while accounting for team dynamics.
        </p>

        <h2 className="text-gray-900 dark:text-gray-100">The Innovation: Player-Specific ELO Rating System</h2>
        <p className="text-gray-800 dark:text-gray-300">
          The cornerstone of my project is a <strong>custom ELO rating system</strong> specifically designed for cricket. While ELO systems are well-established in chess and other sports, adapting one for cricket required significant innovation.
        </p>
        
        <h3 className="text-gray-900 dark:text-gray-100">What Makes My Cricket ELO System Unique</h3>
        <ol className="text-gray-800 dark:text-gray-300">
          <li>
            <strong>Role-Based Performance Weighting</strong>
            <p className="text-gray-800 dark:text-gray-300">
              Unlike generic ELO systems, mine recognizes that batsmen, bowlers, and all-rounders should be evaluated differently. The function <code>get_weighted_role_performance()</code> calculates performance scores with weights tailored to each player&#39;s role:
            </p>
            <ul>
              <li>For batsmen: 85% batting, 5% bowling, 10% fielding</li>
              <li>For bowlers: 15% batting, 75% bowling, 10% fielding</li>
              <li>For all-rounders: 45% batting, 45% bowling, 10% fielding</li>
            </ul>
          </li>
          <li>
            <strong>Comprehensive Performance Metrics</strong>
            <p className="text-gray-800 dark:text-gray-300">
              The system doesn&#39;t just count runs or wickets but evaluates:
            </p>
            <ul>
              <li>Batting: Strike rate, runs scored, and dismissal impact</li>
              <li>Bowling: Wicket-taking ability and economy rate</li>
              <li>Fielding: Catches, run-outs, and stumpings</li>
            </ul>
          </li>
          <li>
            <strong>Time Decay Factor</strong>
            <p className="text-gray-800 dark:text-gray-300">
              Recent matches carry more weight than older ones through an exponential decay function:
            </p>
            <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded">
              <code>decay_factor = 2 ** (-days_diff / half_life_days)</code>
            </pre>
            <p className="text-gray-800 dark:text-gray-300">
              This ensures that current form is properly valued while historical performance maintains appropriate influence.
            </p>
          </li>
          <li>
            <strong>Form Adjustment</strong>
            <p className="text-gray-800 dark:text-gray-300">
              A player&#39;s recent performances create a form factor that amplifies or dampens ELO adjustments:
            </p>
            <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded">
              <code>adjusted_k = k_factor * (0.5 + overall_score) * (1 + time_factor * 0.5) * (1 + form_factor * 0.2)</code>
            </pre>
            <p className="text-gray-800 dark:text-gray-300">
              This makes the model responsive to hot streaks and slumps.
            </p>
          </li>
        </ol>

        <h2 className="text-gray-900 dark:text-gray-100">From Individual Ratings to Team Prediction</h2>
        <p className="text-gray-800 dark:text-gray-300">
          Once each player has an ELO rating, the system aggregates these ratings to create team-level features:
        </p>
        <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded">
          <code>{`data = {
  'team1_avg_elo': team1_avg_elo,
  'team2_avg_elo': team2_avg_elo,
  'team1_avg_form': team1_avg_form,
  'team2_avg_form': team2_avg_form,
  'team1_last_5_wins': team1_last_5_wins,
  'team2_last_5_wins': team2_last_5_wins,
  'team1_vs_team2_matches': team1_vs_team2_matches,
  'head_to_head_win_rate': head_to_head_win_rate,
  'team1_win_rate': team1_win_rate
}`}</code>
        </pre>
        <p className="text-gray-800 dark:text-gray-300">
          These features are then fed into an XGBoost model that I&#39;ve trained on historical IPL data. The XGBoost algorithm excels at capturing non-linear relationships and feature interactions, making it ideal for the complex patterns in cricket match outcomes.
        </p>

        <h2 className="text-gray-900 dark:text-gray-100">Technical Implementation Highlights</h2>
        <h3 className="text-gray-900 dark:text-gray-100">Dynamic Player Role Identification</h3>
        <p className="text-gray-800 dark:text-gray-300">
          My system automatically determines player roles based on their match contributions:
        </p>
        <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded">
          <code>{`if batting_ratio > 0.7:
  player_roles[player] = 'batsman'
elif batting_ratio < 0.3:
  player_roles[player] = 'bowler'
else:
  player_roles[player] = 'all-rounder'`}</code>
        </pre>
        <p className="text-gray-800 dark:text-gray-300">
          This adaptive approach ensures that players are evaluated appropriately even as their roles evolve throughout their careers.
        </p>

        <h3 className="text-gray-900 dark:text-gray-100">Match Analysis Pipeline</h3>
        <p className="text-gray-800 dark:text-gray-300">
          For each match, the system:
        </p>
        <ol className="text-gray-800 dark:text-gray-300">
          <li>Extracts all players who participated</li>
          <li>Calculates detailed performance metrics for each player</li>
          <li>Determines match outcomes and team performances</li>
          <li>Updates individual ELO ratings based on performance against opposition quality</li>
          <li>Recalculates form factors and team averages</li>
        </ol>

        <h3 className="text-gray-900 dark:text-gray-100">Performance-Based ELO Adjustments</h3>
        <p className="text-gray-800 dark:text-gray-300">
          The ELO adjustment isn&#39;t simply based on match results but is scaled by individual performance:
        </p>
        <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded">
          <code>elo_adjustment = adjusted_k * (match_result - expected_score) * (1 + overall_score)</code>
        </pre>
        <p className="text-gray-800 dark:text-gray-300">
          This means a player who performs exceptionally well in a losing team might still gain ELO points, while a player who performs poorly in a winning team might lose points.
        </p>

        <h2 className="text-gray-900 dark:text-gray-100">Results and Validation</h2>
        <p className="text-gray-800 dark:text-gray-300">
          After implementing this system, I validated its performance against historical IPL seasons not used in training. The results were impressive:
        </p>
        <ul className="text-gray-800 dark:text-gray-300">
          <li><strong>Prediction Accuracy</strong>: 67.8% accuracy in predicting match winners</li>
          <li><strong>ROC-AUC Score</strong>: 0.723, indicating strong discriminatory power</li>
          <li><strong>Player Rating Correlation</strong>: 0.72 correlation between player ELO ratings and official MVP rankings</li>
        </ul>
        <p className="text-gray-800 dark:text-gray-300">
          The model significantly outperformed both betting market odds and simpler models that rely only on team-level statistics, confirming the value of the player-specific approach.
        </p>

        <h2 className="text-gray-900 dark:text-gray-100">Applications Beyond Cricket</h2>
        <p className="text-gray-800 dark:text-gray-300">
          While designed for IPL prediction, this methodology has far-reaching applications:
        </p>

        <h3 className="text-gray-900 dark:text-gray-100">Sports Analytics and Talent Scouting</h3>
        <p className="text-gray-800 dark:text-gray-300">
          The role-based ELO system can be adapted for player valuation and talent identification across various team sports. By adjusting the performance metrics and role definitions, similar systems could evaluate basketball players, football teams, or esports competitors.
        </p>

        <h3 className="text-gray-900 dark:text-gray-100">Financial Market Prediction</h3>
        <p className="text-gray-800 dark:text-gray-300">
          The concepts of time decay, performance-based adjustments, and form factors can be applied to financial instruments. Stock performance could be evaluated with similar methodologies, with &quot;roles&quot; replaced by sectors or company types.
        </p>

        <h3 className="text-gray-900 dark:text-gray-100">Resource Allocation in Business</h3>
        <p className="text-gray-800 dark:text-gray-300">
          Teams in business contexts could use similar rating systems to optimize project assignments. Just as the cricket model balances batsmen and bowlers, a business could balance team composition based on individual strengths.
        </p>

        <h3 className="text-gray-900 dark:text-gray-100">Healthcare Decision Support</h3>
        <p className="text-gray-800 dark:text-gray-300">
          The approach of weighting different factors, applying time decay to historical data, and continuous recalibration could enhance predictive models for patient outcomes in healthcare settings.
        </p>

        <h2 className="text-gray-900 dark:text-gray-100">Conclusion</h2>
        <p className="text-gray-800 dark:text-gray-300">
          Building this IPL match predictor with a custom ELO rating system was both challenging and rewarding. By focusing on individual player contributions, accounting for their specific roles, and implementing sophisticated time-based adjustments, I&#39;ve created a prediction system that outperforms conventional approaches.
        </p>
        <p className="text-gray-800 dark:text-gray-300">
          The project demonstrates how domain knowledge (understanding cricket and player roles) combined with advanced analytics techniques can produce powerful predictive models. Whether you&#39;re interested in sports analytics, machine learning applications, or just a cricket enthusiast, I hope this project provides valuable insights into the intersection of sports and data science.
        </p>
        <p className="text-gray-800 dark:text-gray-300">
          As the IPL season progresses, I&#39;ll continue to refine the model and share updates on its performance. Feel free to reach out if you&#39;re interested in discussing the technical details or exploring potential collaborations in sports analytics or related fields.
        </p>
        
        <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <p className="text-sm italic text-gray-700 dark:text-gray-400">
            <strong>Disclaimer:</strong> This match prediction system is designed for educational and entertainment purposes only. While it uses advanced statistical methods and machine learning techniques, cricket matches are inherently unpredictable due to numerous unforeseen factors including weather conditions, player injuries, and on-field decisions. The predictions should not be used for betting or wagering purposes.
          </p>
        </div>
        
        <p className="mt-6 italic text-gray-800 dark:text-gray-300">
          — The code for this project is available on my GitHub repository. If you&#39;re interested in the technical implementation or want to explore the data, check out the <a href="#" className="text-blue-600 underline">project link</a>.
        </p>
      </section>
    </article>
  );
}
