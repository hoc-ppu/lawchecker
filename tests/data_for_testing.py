from copy import deepcopy
from pathlib import Path

from lxml import etree, html

# flake8: noqa

intro_file_1 = Path("example_files/amendments/energy_rm_rep_0904.xml").resolve()
intro_file_2 = Path("example_files/amendments/energy_day_rep_0905.xml").resolve()

intro = html.fromstring(
    f"""<div class="wrap"><section id="intro"><h2>Introduction</h2><p>This report summarises changes between two LawMaker XML official list documents. The documents are:<br/><strong>energy_rm_rep_0904.xml</strong> and <strong>energy_day_rep_0905.xml</strong></p></section><table class="sticky-head table-responsive-md table"><thead><tr><th scope="col"/><th scope="col">energy_rm_rep_0904.xml</th><th scope="col">energy_day_rep_0905.xml</th></tr></thead><tbody><tr><td>File path</td><td>{intro_file_1}</td><td>{intro_file_2}</td></tr><tr><td>Bill Title</td><td>Energy Bill [HL]</td><td>Energy Bill [HL]</td></tr><tr><td>Published date</td><td>Monday 04 September 2023</td><td>Tuesday 05 September 2023</td></tr><tr><td>List Type</td><td>(Amendment Paper)</td><td>(Amendment Paper)</td></tr></tbody></table></div>"""
)

added_and_removed_names_table = html.fromstring(
    """<table class="sticky-head table-responsive-md table an-table"><thead><tr><th scope="col">Ref</th><th scope="col">Names added</th><th scope="col">Names removed</th><th scope="col">Totals</th></tr></thead><tbody><tr><td>NC7</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC13</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC15</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Caroline Lucas</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC17</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC22</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC24</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC25</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC27</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC36</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Kate Osborne</span><span class="col-12 col-lg-6  mb-2">John McDonnell</span><span class="col-12 col-lg-6  mb-2">Caroline Lucas</span><span class="col-12 col-lg-6  mb-2">Kim Johnson</span><span class="col-12 col-lg-6  mb-2">Richard Burgon</span></p></td><td/><td>Added: 5</td></tr><tr><td>NC39</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC40</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Martin Vickers</span><span class="col-12 col-lg-6  mb-2">Mr Philip Hollobone</span><span class="col-12 col-lg-6  mb-2">Simon Hoare</span><span class="col-12 col-lg-6  mb-2">Sir Bill Wiggin</span><span class="col-12 col-lg-6  mb-2">David Mundell</span><span class="col-12 col-lg-6  mb-2">Sir Greg Knight</span></p></td><td/><td>Added: 6</td></tr><tr><td>NC41</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Sir Greg Knight</span><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 3</td></tr><tr><td>NC42</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Sir Greg Knight</span><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 3</td></tr><tr><td>NC46</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC47</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Stewart Malcolm McDonald</span><span class="col-12 col-lg-6  mb-2">Andrew Selous</span><span class="col-12 col-lg-6  mb-2">Simon Fell</span><span class="col-12 col-lg-6  mb-2">Craig Mackinlay</span><span class="col-12 col-lg-6  mb-2">Bob Stewart</span><span class="col-12 col-lg-6  mb-2">Geraint Davies</span><span class="col-12 col-lg-6  mb-2">Clive Efford</span><span class="col-12 col-lg-6  mb-2">Jamie Stone</span><span class="col-12 col-lg-6  mb-2">Antony Higginbotham</span><span class="col-12 col-lg-6  mb-2">David Simmonds</span><span class="col-12 col-lg-6  mb-2">Neil Coyle</span><span class="col-12 col-lg-6  mb-2">Caroline Ansell</span><span class="col-12 col-lg-6  mb-2">James Grundy</span><span class="col-12 col-lg-6  mb-2">John Howell</span><span class="col-12 col-lg-6  mb-2">Mr William Wragg</span><span class="col-12 col-lg-6  mb-2">Andrew Lewer</span><span class="col-12 col-lg-6  mb-2">Sir Bill Wiggin</span><span class="col-12 col-lg-6  mb-2">Wendy Morton</span><span class="col-12 col-lg-6  mb-2">Sir Iain Duncan Smith</span><span class="col-12 col-lg-6  mb-2">Sir Desmond Swayne</span><span class="col-12 col-lg-6  mb-2">Andy Carter</span><span class="col-12 col-lg-6  mb-2">Lia Nici</span><span class="col-12 col-lg-6  mb-2">Mr Ian Liddell-Grainger</span><span class="col-12 col-lg-6  mb-2">Alec Shelbrooke</span><span class="col-12 col-lg-6  mb-2">Sarah Atherton</span><span class="col-12 col-lg-6  mb-2">Scott Benton</span><span class="col-12 col-lg-6  mb-2">Sir Charles Walker</span><span class="col-12 col-lg-6  mb-2">Sir James Duddridge</span><span class="col-12 col-lg-6  mb-2">Mr Tobias Ellwood</span><span class="col-12 col-lg-6  mb-2">Dr Caroline Johnson</span></p></td><td/><td>Added: 31</td></tr><tr><td>NC48</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Caroline Ansell</span><span class="col-12 col-lg-6  mb-2">David Simmonds</span><span class="col-12 col-lg-6  mb-2">Sir Geoffrey Clifton-Brown</span><span class="col-12 col-lg-6  mb-2">Mr David Davis</span><span class="col-12 col-lg-6  mb-2">Scott Benton</span></p></td><td/><td>Added: 5</td></tr><tr><td>NC49</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC50</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Martin Vickers</span><span class="col-12 col-lg-6  mb-2">Simon Hoare</span></p></td><td/><td>Added: 2</td></tr><tr><td>NC51</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Kate Hollern</span></p></td><td/><td>Added: 1</td></tr><tr><td>NC53</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p></td><td>Olivia Blake</td><td>Added: 1, Removed: 1</td></tr><tr><td>NC58</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p></td><td>Olivia Blake</td><td>Added: 1, Removed: 1</td></tr><tr><td>NC59</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p></td><td>Olivia Blake</td><td>Added: 1, Removed: 1</td></tr><tr><td>NC60</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Sir Iain Duncan Smith</span><span class="col-12 col-lg-6  mb-2">Lia Nici</span><span class="col-12 col-lg-6  mb-2">Tim Loughton</span></p></td><td/><td>Added: 3</td></tr><tr><td>NC67</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Hywel Williams</span><span class="col-12 col-lg-6  mb-2">Liz Saville Roberts</span><span class="col-12 col-lg-6  mb-2">Ben Lake</span><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td/><td>Added: 4</td></tr><tr><td>NC68</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td/><td>Added: 1</td></tr><tr><td>9</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>10</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>11</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>12</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>13</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>14</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>15</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>16</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>17</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>18</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>19</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>20</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>21</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>22</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>23</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>24</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>25</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>26</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>27</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>28</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>29</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>30</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>31</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>32</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>33</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>34</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>35</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>36</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>37</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>38</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>39</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>40</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>41</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>42</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>43</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>44</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>45</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>46</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>47</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>48</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>49</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>8</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Martin Vickers</span><span class="col-12 col-lg-6  mb-2">Sir Bill Wiggin</span><span class="col-12 col-lg-6  mb-2">David Mundell</span></p></td><td/><td>Added: 3</td></tr><tr><td>50</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>51</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>52</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>53</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>54</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>55</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>56</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>57</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>58</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>59</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>60</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>61</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>62</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>63</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>64</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>65</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>66</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span><span class="col-12 col-lg-6  mb-2">Anne Marie Morris</span><span class="col-12 col-lg-6  mb-2">Lia Nici</span><span class="col-12 col-lg-6  mb-2">Dame Andrea Jenkyns</span><span class="col-12 col-lg-6  mb-2">Miriam Cates</span><span class="col-12 col-lg-6  mb-2">Sir Robert Syms</span><span class="col-12 col-lg-6  mb-2">Adam Holloway</span><span class="col-12 col-lg-6  mb-2">Damien Moore</span></p></td><td/><td>Added: 9</td></tr><tr><td>67</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>68</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr><tr><td>69</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td/><td>Added: 2</td></tr></tbody></table>
"""
)

intro_input = etree.fromstring(
"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://docs.oasis-open.org/legaldocml/ns/akn/3.0 ../schemas/akomantoso30.xsd">
<?LDAPP-Component componentId="" ?>
	<amendmentList contains="originalVersion" name="hcmarsh">
	 <meta>
	  <identification source="#source">

	   <!-- good -->
	   <FRBRManifestation>
		<FRBRdate date="2023-09-04" name="published"/>
	   </FRBRManifestation>
	   <!-- g -->
	  </identification>
	  <references source="#author">

		<!-- good -->
	   <TLCConcept eId="varBillTitle" href="#varOntologies" showAs="Energy Bill [HL]"/>
	   <!-- g -->

	   <TLCProcess eId="varStageVersion" href="#varOntologies" showAs="Report Stage"/>

	  </references>
	 </meta>
	 <preface eId="preface">
		<!-- good -->
		<block name="listType">(Amendment Paper)</block>
		<!-- g -->
	 </preface>
	</amendmentList>
</akomaNtoso>"""
)


added_names_table = html.fromstring(
    """<table class="an-table table-responsive-md table"><thead><tr><th>Ref</th><th>Names added</th><th>Names removed</th><th>Totals</th></tr></thead><tbody><tr><td>NC7</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC13</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC15</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Caroline Lucas</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC17</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC22</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC24</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC25</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC27</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Wendy Chamberlain</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC36</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Kate Osborne</span><span class="col-12 col-lg-6  mb-2">John McDonnell</span><span class="col-12 col-lg-6  mb-2">Caroline Lucas</span><span class="col-12 col-lg-6  mb-2">Kim Johnson</span><span class="col-12 col-lg-6  mb-2">Richard Burgon</span></p></td><td></td><td><p>Added: 5</p></td></tr><tr><td>NC39</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC40</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Martin Vickers</span><span class="col-12 col-lg-6  mb-2">Mr Philip Hollobone</span><span class="col-12 col-lg-6  mb-2">Simon Hoare</span><span class="col-12 col-lg-6  mb-2">Sir Bill Wiggin</span><span class="col-12 col-lg-6  mb-2">David Mundell</span><span class="col-12 col-lg-6  mb-2">Sir Greg Knight</span></p></td><td></td><td><p>Added: 6</p></td></tr><tr><td>NC41</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Sir Greg Knight</span><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 3</p></td></tr><tr><td>NC42</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Sir Greg Knight</span><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 3</p></td></tr><tr><td>NC46</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC47</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Stewart Malcolm McDonald</span><span class="col-12 col-lg-6  mb-2">Andrew Selous</span><span class="col-12 col-lg-6  mb-2">Simon Fell</span><span class="col-12 col-lg-6  mb-2">Craig Mackinlay</span><span class="col-12 col-lg-6  mb-2">Bob Stewart</span><span class="col-12 col-lg-6  mb-2">Geraint Davies</span><span class="col-12 col-lg-6  mb-2">Clive Efford</span><span class="col-12 col-lg-6  mb-2">Jamie Stone</span><span class="col-12 col-lg-6  mb-2">Antony Higginbotham</span><span class="col-12 col-lg-6  mb-2">David Simmonds</span><span class="col-12 col-lg-6  mb-2">Neil Coyle</span><span class="col-12 col-lg-6  mb-2">Caroline Ansell</span><span class="col-12 col-lg-6  mb-2">James Grundy</span><span class="col-12 col-lg-6  mb-2">John Howell</span><span class="col-12 col-lg-6  mb-2">Mr William Wragg</span><span class="col-12 col-lg-6  mb-2">Andrew Lewer</span><span class="col-12 col-lg-6  mb-2">Sir Bill Wiggin</span><span class="col-12 col-lg-6  mb-2">Wendy Morton</span><span class="col-12 col-lg-6  mb-2">Sir Iain Duncan Smith</span><span class="col-12 col-lg-6  mb-2">Sir Desmond Swayne</span><span class="col-12 col-lg-6  mb-2">Andy Carter</span><span class="col-12 col-lg-6  mb-2">Lia Nici</span><span class="col-12 col-lg-6  mb-2">Mr Ian Liddell-Grainger</span><span class="col-12 col-lg-6  mb-2">Alec Shelbrooke</span><span class="col-12 col-lg-6  mb-2">Sarah Atherton</span><span class="col-12 col-lg-6  mb-2">Scott Benton</span><span class="col-12 col-lg-6  mb-2">Sir Charles Walker</span><span class="col-12 col-lg-6  mb-2">Sir James Duddridge</span><span class="col-12 col-lg-6  mb-2">Mr Tobias Ellwood</span><span class="col-12 col-lg-6  mb-2">Dr Caroline Johnson</span></p></td><td></td><td><p>Added: 31</p></td></tr><tr><td>NC48</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Caroline Ansell</span><span class="col-12 col-lg-6  mb-2">David Simmonds</span><span class="col-12 col-lg-6  mb-2">Sir Geoffrey Clifton-Brown</span><span class="col-12 col-lg-6  mb-2">Mr David Davis</span><span class="col-12 col-lg-6  mb-2">Scott Benton</span></p></td><td></td><td><p>Added: 5</p></td></tr><tr><td>NC49</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC50</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Martin Vickers</span><span class="col-12 col-lg-6  mb-2">Simon Hoare</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>NC51</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Kate Hollern</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>NC53</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p></td><td>Olivia Blake</td><td><p>Added: 1<br/>Removed: 1</p></td></tr><tr><td>NC58</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p></td><td>Olivia Blake</td><td><p>Added: 1<br/>Removed: 1</p></td></tr><tr><td>NC59</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p></td><td>Olivia Blake</td><td><p>Added: 1<br/>Removed: 1</p></td></tr><tr><td>NC60</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Sir Iain Duncan Smith</span><span class="col-12 col-lg-6  mb-2">Lia Nici</span><span class="col-12 col-lg-6  mb-2">Tim Loughton</span></p></td><td></td><td><p>Added: 3</p></td></tr><tr><td>NC67</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Hywel Williams</span><span class="col-12 col-lg-6  mb-2">Liz Saville Roberts</span><span class="col-12 col-lg-6  mb-2">Ben Lake</span><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td></td><td><p>Added: 4</p></td></tr><tr><td>NC68</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Dave Doogan</span></p></td><td></td><td><p>Added: 1</p></td></tr><tr><td>9</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>10</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>11</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>12</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>13</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>14</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>15</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>16</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>17</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>18</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>19</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>20</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>21</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>22</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>23</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>24</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>25</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>26</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>27</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>28</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>29</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>30</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>31</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>32</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>33</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>34</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>35</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>36</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>37</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>38</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>39</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>40</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>41</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>42</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>43</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>44</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>45</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>46</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>47</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>48</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>49</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>8</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">Martin Vickers</span><span class="col-12 col-lg-6  mb-2">Sir Bill Wiggin</span><span class="col-12 col-lg-6  mb-2">David Mundell</span></p></td><td></td><td><p>Added: 3</p></td></tr><tr><td>50</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>51</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>52</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>53</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>54</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>55</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>56</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>57</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>58</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>59</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>60</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>61</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>62</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>63</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>64</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>65</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>66</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span><span class="col-12 col-lg-6  mb-2">Anne Marie Morris</span><span class="col-12 col-lg-6  mb-2">Lia Nici</span><span class="col-12 col-lg-6  mb-2">Dame Andrea Jenkyns</span><span class="col-12 col-lg-6  mb-2">Miriam Cates</span><span class="col-12 col-lg-6  mb-2">Sir Robert Syms</span><span class="col-12 col-lg-6  mb-2">Adam Holloway</span><span class="col-12 col-lg-6  mb-2">Damien Moore</span></p></td><td></td><td><p>Added: 9</p></td></tr><tr><td>67</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>68</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr><tr><td>69</td><td><p class="row"><span class="col-12 col-lg-6  mb-2">John Redwood</span><span class="col-12 col-lg-6  mb-2">Mr David Jones</span></p></td><td></td><td><p>Added: 2</p></td></tr></tbody></table>"""
)


energy_0904_nc53 = etree.fromstring(
	"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <amendmentList>
	<collectionBody>
	  <component class="amendment" ukl:statusIndicator="☆">
      <amendment>
     <preface GUID="_c8843e36-c036-4b47-bb72-c3b1a79d48ea" eId="amnd_NC53__fnt">
      <block name="title"><affectedDocument href="https://lawmaker.legislation.gov.uk/pdr/UK000258/bill@public-committee-hc"><ref class="placeholder" href="#varBillTitle"/></affectedDocument> — <docStage>Report Stage</docStage></block>
     </preface>
     <amendmentBody GUID="_1416be71-5296-40ef-a14d-5bfb031a10f1" eId="amnd_NC53" ukl:location="" ukl:targetPage="" ukl:targetProvision="" ukl:targetSortKey="A53" ukl:type="newClause">
      <amendmentHeading GUID="_6d4974dc-6a32-49c1-a285-83fe3b41e2ac" eId="amnd_NC53__hdg">
       <block name="proposer"><docIntroducer refersTo="amnd_NC53#person-1510">Edward Miliband</docIntroducer></block>
       <block name="supporters"><docProponent refersTo="amnd_NC53#person-62">Dr Alan Whitehead</docProponent><docProponent refersTo="amnd_NC53#person-1491">Kerry McCarthy</docProponent><docProponent refersTo="amnd_NC53#person-4864">Olivia Blake</docProponent></block>
      </amendmentHeading>
      <amendmentContent GUID="_f111e95b-34e0-4061-b465-ba842a419502" eId="amnd_NC53__cont">
       <tblock>
        <num ukl:dnum="HoC230">NC53</num>
        <block name="instruction"><mod>To move the following Clause—<quotedStructure GUID="_b7580a50-6212-4924-9f48-27c6f5a2e3f4" eId="amnd_NC53__cont__qstr" endQuote="”" startQuote="“" ukl:context="body" ukl:docName="ukpga" ukl:indent="indent0">
         <section GUID="_5e4994cf-f567-4269-9e21-233b295b7241" class="prov1" eId="amnd_NC53__cont__qstr__sec">
          <num/>
          <heading GUID="_1457becd-d546-4c02-ae1d-d106a2fb82d9" eId="amnd_NC53__cont__qstr__sec__hdg">Community and Smaller-scale Electricity Supplier Services Scheme</heading>
         </section>
         </quotedStructure><inline name="AppendText"/></mod> </block>
       </tblock>
      </amendmentContent>
     </amendmentBody>
    </amendment>
	</component>
	</collectionBody>
  </amendmentList>
</akomaNtoso>"""
)
energy_0905_nc53 = deepcopy(energy_0904_nc53)
# print(len(energy_0905_nc53.xpath('//docProponent[@refersTo]')))
energy_0905_nc53.find('.//docProponent[@refersTo="amnd_NC53#person-4864"]', namespaces={None:"http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}).text = "Olivia Blake [R]"

added_and_removed_names_section = etree.fromstring(
    '''<section class="card">
<div class="card-inner collapsible">
  <div class="collapsible-header">
  <h2 data-heading-label="Added and removed names" id="card-1"><span class="arrow"> </span>Added and removed names<small class="text-muted"> [hide]</small></h2>
  </div>
  <div class="collapsible-content">
  <div class="content">
    <div class="secondary-info">
    <!-- This is where secondary info goes -->
  <table class="sticky-head table-responsive-md table an-table">
        <thead>
        <tr>
          <th scope="col">Ref</th>
          <th scope="col">Names added</th>
          <th scope="col">Names removed</th>
          <th scope="col">Totals</th>
        </tr>
        </thead>
        <tbody>
        <tr>
          <td>NC53</td>
          <td>
          <p class="row"><span class="col-12 col-lg-6  mb-2">Olivia Blake [R]</span></p>
          </td>
          <td>Olivia Blake</td>
          <td>Added: 1, Removed: 1</td>
        </tr>
        </tbody>
  </table>
  <section class="collapsible closed">
  <div class="collapsible-header">
  <h3 class="h4"><span class="arrow"> </span>Name Changes in Context <small class="text-muted"> [show]</small></h3>
  <p>Expand this section to see the same names as above but in context.</p>
  </div>
  <div class="collapsible-content" style="display: none;" id="name-changes-in-context">
  <p><strong>1</strong> amendments have changed names: </p>
  <div>
  <p class="h5 mt-4">NC53:</p>
  <table class="diff" id="difflib_chg_to0__top" cellspacing="0" cellpadding="0" rules="groups">
  <colgroup></colgroup><colgroup></colgroup><colgroup></colgroup><colgroup></colgroup><colgroup></colgroup><colgroup></colgroup><thead><tr><th class="diff_next"><br/></th><th colspan="2" class="diff_header">Test</th><th class="diff_next"><br/></th><th colspan="2" class="diff_header">Test</th></tr></thead><tbody><tr><td class="diff_next" id="difflib_chg_to0__0"><a href="#difflib_chg_to0__0">f</a></td><td class="diff_header" id="from0_1">1</td><td>Edward Miliband</td><td class="diff_next"><a href="#difflib_chg_to0__0">f</a></td><td class="diff_header" id="to0_1">1</td><td>Edward Miliband</td></tr><tr><td class="diff_next"></td><td class="diff_header" id="from0_2">2</td><td>Dr Alan Whitehead</td><td class="diff_next"></td><td class="diff_header" id="to0_2">2</td><td>Dr Alan Whitehead</td></tr><tr><td class="diff_next"></td><td class="diff_header" id="from0_3">3</td><td>Kerry McCarthy</td><td class="diff_next"></td><td class="diff_header" id="to0_3">3</td><td>Kerry McCarthy</td></tr><tr><td class="diff_next"><a href="#difflib_chg_to0__top">t</a></td><td class="diff_header" id="from0_4">4</td><td>Olivia Blake</td><td class="diff_next"><a href="#difflib_chg_to0__top">t</a></td><td class="diff_header" id="to0_4">4</td><td>Olivia Blake<span class="diff_add"> [R]</span></td></tr></tbody></table>
  </div>
  </div>
    </section>
    </div>
  </div>
  <div class="info">
    <div class="info-inner">
    <!-- Tertiary info -->
      <p><strong>Zero</strong> amendments have no name changes.</p>
    </div>
  </div>
  </div>
</div>
</section>
'''
)

dummy_amendment_with_black_star = etree.fromstring(
    """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

	<amendmentList>
	 <collectionBody>
	  <component class="amendment" ukl:statusIndicator="★">
	   <amendment name="hcamnd">
		<preface>
		 <block name="title"> — <docStage>Report Stage</docStage></block>
		</preface>
		<amendmentBody>
		 <amendmentHeading>
		  <block name="proposer"><docIntroducer refersTo="">Secretary Claire Coutinho</docIntroducer></block>
		 </amendmentHeading>
		 <amendmentContent>
		  <tblock>
		   <num ukl:dnum="">NC52</num>
		   <block name="instruction"><mod>To move the following Clause—<quotedStructure endQuote="”" startQuote="“">
			<section>
			 <num/>
			 <heading>Revenue certainty scheme for sustainable aviation fuel producers: consultation and report</heading>
			</section>
			</quotedStructure><inline name="AppendText"/></mod> </block>
		  </tblock>
		 </amendmentContent>
		 <amendmentJustification>
		  <blockContainer><heading>Member's explanatory statement</heading>
		   <p>explanatory statement</p>
		  </blockContainer>
		 </amendmentJustification>
		</amendmentBody>
	   </amendment>
	  </component>
	 </collectionBody>
	</amendmentList>
</akomaNtoso>"""
)

dummy_amendment_with_white_star = etree.fromstring(
    """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

	<amendmentList>
	 <collectionBody>
	  <component class="amendment" ukl:statusIndicator="☆">
	   <amendment name="hcamnd">
		<preface>
		 <block name="title"> — <docStage>Report Stage</docStage></block>
		</preface>
		<amendmentBody>
		 <amendmentHeading>
		  <block name="proposer"><docIntroducer refersTo="">Secretary Claire Coutinho</docIntroducer></block>
		 </amendmentHeading>
		 <amendmentContent>
		  <tblock>
		   <num ukl:dnum="">NC52</num>
		   <block name="instruction"><mod>To move the following Clause—<quotedStructure endQuote="”" startQuote="“">
			<section>
			 <num/>
			 <heading>Revenue certainty scheme for sustainable aviation fuel producers: consultation and report</heading>
			</section>
			</quotedStructure><inline name="AppendText"/></mod> </block>
		  </tblock>
		 </amendmentContent>
		 <amendmentJustification>
		  <blockContainer><heading>Member's explanatory statement</heading>
		   <p>explanatory statement</p>
		  </blockContainer>
		 </amendmentJustification>
		</amendmentBody>
	   </amendment>
	  </component>
	 </collectionBody>
	</amendmentList>
</akomaNtoso>"""
)

dummy_amendment_with_no_star = etree.fromstring("""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

	<amendmentList>
	 <collectionBody>
	  <component class="amendment">
	   <amendment name="hcamnd">
		<preface>
		 <block name="title"> — <docStage>Report Stage</docStage></block>
		</preface>
		<amendmentBody>
		 <amendmentHeading>
		  <block name="proposer"><docIntroducer refersTo="">Secretary Claire Coutinho</docIntroducer></block>
		 </amendmentHeading>
		 <amendmentContent>
		  <tblock>
		   <num ukl:dnum="">NC52</num>
		   <block name="instruction"><mod>To move the following Clause—<quotedStructure endQuote="”" startQuote="“">
			<section>
			 <num/>
			 <heading>Revenue certainty scheme for sustainable aviation fuel producers: consultation and report</heading>
			</section>
			</quotedStructure><inline name="AppendText"/></mod> </block>
		  </tblock>
		 </amendmentContent>
		 <amendmentJustification>
		  <blockContainer><heading>Member's explanatory statement</heading>
		   <p>explanatory statement</p>
		  </blockContainer>
		 </amendmentJustification>
		</amendmentBody>
	   </amendment>
	  </component>
	 </collectionBody>
	</amendmentList>
</akomaNtoso>"""
)


dummy_amendment_with_unknown_star = etree.fromstring("""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

	<amendmentList>
	 <collectionBody>
	  <component class="amendment" ukl:statusIndicator="UNKNOWN STAR">
	   <amendment name="hcamnd">
		<preface>
		 <block name="title"> — <docStage>Report Stage</docStage></block>
		</preface>
		<amendmentBody>
		 <amendmentHeading>
		  <block name="proposer"><docIntroducer refersTo="">Secretary Claire Coutinho</docIntroducer></block>
		 </amendmentHeading>
		 <amendmentContent>
		  <tblock>
		   <num ukl:dnum="">NC52</num>
		   <block name="instruction"><mod>To move the following Clause—<quotedStructure endQuote="”" startQuote="“">
			<section>
			 <num/>
			 <heading>Revenue certainty scheme for sustainable aviation fuel producers: consultation and report</heading>
			</section>
			</quotedStructure><inline name="AppendText"/></mod> </block>
		  </tblock>
		 </amendmentContent>
		 <amendmentJustification>
		  <blockContainer><heading>Member's explanatory statement</heading>
		   <p>explanatory statement</p>
		  </blockContainer>
		 </amendmentJustification>
		</amendmentBody>
	   </amendment>
	  </component>
	 </collectionBody>
	</amendmentList>
</akomaNtoso>"""
)
