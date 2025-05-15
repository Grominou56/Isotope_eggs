import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt

# -----------------------------
# 1. Génération de données fictives
# -----------------------------
np.random.seed(0)
n_sites = 150

# Températures mensuelles (T1 à T12)
temps = np.random.uniform(-5, 30, size=(n_sites, 12))
# Précipitations mensuelles (P1 à P12)
precip = np.random.uniform(10, 200, size=(n_sites, 12))
# δ18O de l'eau (mensuel)
d18O_water = np.random.uniform(-12, 0, size=(n_sites, 12))

# Génération d'un δ18O apatite réaliste : moyenne pondérée par la température
d18O_apatite = (
    (d18O_water * temps).sum(axis=1) / temps.sum(axis=1) +
    np.random.normal(0, 0.5, size=n_sites)
)

# -----------------------------
# 2. Construction du DataFrame avec blocs mensuels (T, P, δ18O eau)
# -----------------------------
columns = []
X_data = []

for i in range(12):
    columns.extend([f"T{i+1}", f"P{i+1}", f"d18Ow{i+1}"])
    for site in range(n_sites):
        if i == 0:
            X_data.append([])  # créer une ligne par site
        X_data[site].extend([temps[site, i], precip[site, i], d18O_water[site, i]])

X_df = pd.DataFrame(X_data, columns=columns)
X_df["d18O_apatite"] = d18O_apatite

# -----------------------------
# 3. Modélisation Random Forest
# -----------------------------
X = X_df.drop(columns=["d18O_apatite"])
y = X_df["d18O_apatite"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=0
)

model = RandomForestRegressor(n_estimators=100, random_state=0)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# -----------------------------
# 4. Évaluation du modèle
# -----------------------------
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"R² : {r2:.3f}")
print(f"RMSE : {rmse:.3f} ‰")

# -----------------------------
# 5. Importance des mois (somme des 3 variables par mois)
# -----------------------------
importances = model.feature_importances_
importances_monthly = {
    f"Mois {i+1}": sum(importances[i*3:(i+1)*3]) for i in range(12)
}
importances_monthly = pd.Series(importances_monthly).sort_values(ascending=False)

print("\nImportance des mois :")
print(importances_monthly)

# -----------------------------
# 6. Graphique prédiction vs réalité
# -----------------------------
plt.figure(figsize=(6, 6))
plt.scatter(y_test, y_pred, alpha=0.7)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel("δ18O apatite réel")
plt.ylabel("δ18O apatite prédit")
plt.title("Random Forest - Prédiction avec blocs mensuels")
plt.grid(True)
plt.tight_layout()
plt.show()
