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
    <?php
      echo "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
         . "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
         . "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
         . "nisi ut aliquip ex ea commodo consequat.";
    ?>
  </p>
  <img src="image.png" alt="Sample Image" />

  <!-- Button to invoke the Lambda via API Gateway -->
  <button id="fetchBtn">Fetch VPC & Subnets Inventory</button>
  <div id="inventory"></div>

  <script>
    const apiUrl = "<?php echo getenv('INVENTORY_API_URL'); ?>";
    
    function renderTable(data, columns, title) {
      let html = `<h2>${title}</h2><table><thead><tr>`;
      columns.forEach(col => html += `<th>${col}</th>`);
      html += `</tr></thead><tbody>`;
      data.forEach(item => {
        html += `<tr>`;
        columns.forEach(col => {
          let val = item[col] !== undefined ? item[col] : '';
          if (typeof val === 'object') val = JSON.stringify(val);
          html += `<td>${val}</td>`;
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
          let html = `<p>Fetched at: ${data.timestamp}</p>`;
          html += renderTable(data.vpcs.map(v => ({
            VpcId: v.VpcId,
            CidrBlock: v.CidrBlock,
            IsDefault: v.IsDefault,
            Tags: v.Tags
          })), ['VpcId','CidrBlock','IsDefault','Tags'], 'VPCs');
          html += renderTable(data.subnets.map(s => ({
            SubnetId: s.SubnetId,
            VpcId: s.VpcId,
            CidrBlock: s.CidrBlock,
            AvailabilityZone: s.AvailabilityZone,
            MapPublicIpOnLaunch: s.MapPublicIpOnLaunch,
            Tags: s.Tags
          })), ['SubnetId','VpcId','CidrBlock','AvailabilityZone','MapPublicIpOnLaunch','Tags'], 'Subnets');
          out.innerHTML = html;
        })
        .catch(err => {
          out.textContent = 'Error fetching inventory: ' + err;
        });
    });
  </script>
</body>
</html>
