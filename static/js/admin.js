
function admin_reorder_swap(e,s,t) {
    let listelem = e.target.parentNode;
    let listmain = listelem.parentNode
    let listelems = listmain.querySelectorAll(t);
    for (let i = 0; i < listelems.length; ++i) {
        if (listelems[i] === listelem) {
            let j = i + s;
            if (j >= 0 && j < listelems.length) {
                let listelem2 = listelems[j];
                if (i < j)
                    listmain.insertBefore(listelem2,listelem);
                else
                    listmain.insertBefore(listelem,listelem2);
                return;
            }
        }
    }
}

function make_reorder_list_post_data() {
    let s = '';
    document.querySelectorAll('#admin_reorder_list li').forEach(li => {
        s += li.querySelector('span').innerHTML + '\n';
    });
    document.querySelector('#output_reorder_list').value = s;
}

function append_nums_table_row() {
    let row = document.createElement('tr');
    row.innerHTML = `
        <td><input type="text" placeholder="index" /></td>
        <td><input type="text" placeholder="expr" /></td>
        <td><input type="text" placeholder="value" /></td>
        <td><input type="text" placeholder="factors" /></td>
        <td><button>delete</button></td>`;
    row.querySelector('button').addEventListener('click', () => row.remove());
    document.querySelector('#admin_add_nums_table').appendChild(row);
}

function make_add_nums_inputs() {
    let form = document.querySelector('#admin_add_nums_form');
    document.querySelectorAll('#admin_add_nums_table tr').forEach((row,i) => {
        let inps = row.querySelectorAll('input');
        let inp0 = document.createElement('input');
        inp0.type = 'hidden';
        inp0.name = 'index' + String(i);
        inp0.value = inps[0].value;
        let inp1 = document.createElement('input');
        inp1.type = 'hidden';
        inp1.name = 'expr' + String(i);
        inp1.value = inps[1].value;
        let inp2 = document.createElement('input');
        inp2.type = 'hidden';
        inp2.name = 'value' + String(i);
        inp2.value = inps[2].value;
        let inp3 = document.createElement('input');
        inp3.type = 'hidden';
        inp3.name = 'factors' + String(i);
        inp3.value = inps[3].value;
        form.appendChild(inp0);
        form.appendChild(inp1);
        form.appendChild(inp2);
        form.appendChild(inp3);
    });
}
