<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Lorem Ipsum PHP Site</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    img  { max-width: 300px; display: block; margin-top: 20px; }
    #inventory { margin-top: 20px; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    button { padding: 10px 20px; font-size: 1rem; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Welcome to the Lorem Ipsum PHP Site</h1>
  <p>
    <?php echo "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " .
                 "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."; ?>
  </p>
  <img src="image.png" alt="Sample Image" />

  <!-- Fetch Inventory Button -->
  <button id="fetchBtn">Fetch VPC & Subnets Inventory</button>
  <div id="inventory"></div>

  <script>
    const apiUrl = "<?php echo getenv('INVENTORY_API_URL'); ?>";
    
    function renderTable(data, cols, title) {
      let html = `<h2>${title}</h2><table><thead><tr>`;
      cols.forEach(c => html += `<th>${c}</th>`);
      html += `</tr></thead><tbody>`;
      data.forEach(item => {
        html += `<tr>`;
        cols.forEach(c => {
          let v = item[c] !== undefined ? item[c] : '';
          if (typeof v === 'object') v = JSON.stringify(v);
          html += `<td>${v}</td>`;
        });
        html += `</tr>`;
      });
      html += `</tbody></table>`;
      return html;
    }

    document.getElementById('fetchBtn').addEventListener('click', () => {
      const out = document.getElementById('inventory');
      out.innerHTML = 'Loading…';
      fetch(apiUrl)
        .then(response => {
          if (!response.ok) throw new Error(response.status + ' ' + response.statusText);
          return response.json();
        })
        .then(data => {
          console.log('Received data:', data);
          let content = `<p>Fetched at: ${data.timestamp}</p>`;
          content += renderTable(data.vpcs, ['VpcId','CidrBlock','IsDefault','Tags'], 'VPCs');
          content += renderTable(data.subnets, ['SubnetId','VpcId','CidrBlock','AvailabilityZone','MapPublicIpOnLaunch','Tags'], 'Subnets');
          out.innerHTML = content;
        })
        .catch(e => {
          console.error('Fetch error:', e);
          out.textContent = 'Error fetching inventory: ' + e;
        });
    });
  </script>
</body>
</html>
