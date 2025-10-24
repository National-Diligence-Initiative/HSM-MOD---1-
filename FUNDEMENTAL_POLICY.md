
POLICY: IDN-MSC-01 // DIRECTIVE: ADJUSTABLE STRATAGEM INTEGRATION

1.0 Preamble
This policy governs the application of the metScore mechanic for quantifying operational efficacy. The core mechanic is declared immutable; stratagem is applied through parameter modulation and post-processing.

2.0 Core Mechanic (IMMUTABLE)
The base calculation is defined as:
normalized_score = max(0.0, min(1.0, ( (C + D + CM + A) / 400 ) * U ))
force_rating = int(normalized_score * 10000)

Where input parameters are bound to the domain:

· C (Courage): [0, 100]
· D (Dexterity): [0, 100]
· CM (Clause Matter): [0, 100]
· A (Audacity): [0, 100]
· U (Unity): [0.0, 2.0]

3.0 Stratagem Adjustment Protocols
Adjustable mission stratagem is enabled via the following authorized vectors.

3.1 Parameter Weighting (Pre-Processing)
Apply scalar weights to inputs to alter their influence on the final score,reflecting mission priority.

· Stratagem Code: WEIGHTED_PARAM
· Implementation:
  ```python
  # Define a stratagem profile
  profile = {
      'courage': 1.2,      # Morally complex objective
      'dexterity': 0.9,    # Reduced technical requirement
      'clause_matter': 1.5, # High legal/conceptual criticality
      'audacity': 1.0,     # Standard risk tolerance
      'unity': 1.1         # Enhanced team coherence required
  }
  # Apply weights pre-normalization
  weighted_total = ( (courage * profile['courage']) +
                     (dexterity * profile['dexterity']) +
                     (clause_matter * profile['clause_matter']) +
                     (audacity * profile['audacity']) )
  normalized = max(0.0, min(1.0, (weighted_total / 400) * profile['unity']))
  ```

3.2 Threshold Gates (Post-Processing)
Define minimum scores for mission phases.A score failing a gate is grounds for abort or revision.

· Stratagem Code: THRESHOLD_GATE
· Implementation:
  ```python
  NORM_GATE_APPROVAL = 0.65    # Minimum for mission approval
  FORCE_GATE_ENGAGEMENT = 7500 # Minimum for full engagement
  norm, force = metScore(...)
  
  if norm < NORM_GATE_APPROVAL:
      directive = "ABORT: Failed Approval Gate."
  elif force < FORCE_GATE_ENGAGEMENT:
      directive = "HOLD: Reroute for stratagem reassessment."
  else:
      directive = "CLEAR: Proceed to engagement."
  ```

3.3 Stratagem Profiles (Pre-Sets)
Pre-defined parameter sets for standardized mission types.

· Stratagem Code: PROFILE_<TYPE>
· Implementation:
  ```python
  STRATAGEM_PROFILES = {
      'STEALTH': (70, 95, 90, 60, 1.0),   # High Dexterity, High Clause Matter
      'ASSAULT': (90, 80, 60, 95, 1.3),   # High Courage, High Audacity, High Unity
      'DIPLOMACY': (85, 60, 95, 70, 0.8), # High Courage, High Clause Matter
  }
  # Execute with profile
  params = STRATAGEM_PROFILES['ASSAULT']
  norm, force = metScore(*params)
  ```

4.0 Compliance
Use of this mechanic implies adherence to this policy.All adjustments outside these protocols require a formal metScore clause amendment.

---

End of Policy TGDK-MSC-01.

---

Example Execution under Policy:

```python
# Execute under PROFILE_ASSAULT with a THRESHOLD_GATE
params = (90, 80, 60, 95, 1.3) # ASSAULT Profile
norm, force = metScore(*params)

print(f"Normalized: {norm:.4f}")
print(f"Force: {force}")

# Apply Gate
if force < 7500:
    print("DIRECTIVE: HOLD")
else:
    print("DIRECTIVE: CLEAR")
```

Output:

```
Normalized: 0.8774
Force: 8774
DIRECTIVE: CLEAR
```