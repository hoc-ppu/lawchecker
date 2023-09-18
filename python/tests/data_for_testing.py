from lxml import etree, html

intro = html.fromstring(
    """<div class="wrap"><section id="intro"><h2>Introduction</h2><p>This report summarises changes between two LawMaker XML official list documents. The documents are:<br/><strong>energy_rm_rep_0904.xml</strong> and <strong>energy_day_rep_0905.xml</strong></p></section><table class="sticky-head table-responsive-md table"><thead><tr><th scope="col"/><th scope="col">energy_rm_rep_0904.xml</th><th scope="col">energy_day_rep_0905.xml</th></tr></thead><tbody><tr><td>File path</td><td>/Users/mark/projects/check_amendment_papers/LM_XML/energy_rm_rep_0904.xml</td><td>/Users/mark/projects/check_amendment_papers/LM_XML/energy_day_rep_0905.xml</td></tr><tr><td>Bill Title</td><td>Energy Bill [HL]</td><td>Energy Bill [HL]</td></tr><tr><td>Published date</td><td>Monday 04 September 2023</td><td>Tuesday 05 September 2023</td></tr><tr><td>List Type</td><td>(Amendment Paper)</td><td>(Amendment Paper)</td></tr></tbody></table></div>"""
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
