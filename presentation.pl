#!/usr/bin/env perl
use strict;
use warnings;
use Curses;

my $window;
use FileHandle;
use Carp;

sub strip_tags {
    my ($text) = @_;
    $text =~ s/<[^>]+>//g;
    return $text;
}

sub is_subpage {
    my ($line) = @_;
    return strip_tags($line) =~ /^\s*- /;
}

sub initialize_curses {
    initscr();
    cbreak();
    noecho();
    keypad(1);
    start_color();
    use_default_colors();
    init_pair(1, COLOR_YELLOW, -1);
    init_pair(2, COLOR_GREEN, -1);
    init_pair(3, COLOR_MAGENTA, -1);
    $window = Curses->new;
}

sub cleanup_curses {
    endwin();
}

sub print_page {
    my ($page_content, $visible_subpages) = @_;
    $window->clear();
    my $y = 0;
    my $current_color = 0;
    my @lines = split /\n/, $page_content;
    my $in_subpage_section = 0;
    my $subpages_printed = 0;
    my $total_subpages = 0;
    my @subpage_content;
    
    foreach my $line (@lines) {
        if ($line =~ /^\s*$/) {
            push @subpage_content, $line if !$in_subpage_section || $subpages_printed > 0;
            next;
        }

        my $is_subpage = is_subpage($line);
        if ($is_subpage) {
            $in_subpage_section = 1;
            $total_subpages++;
            if ($subpages_printed < $visible_subpages) {
                push @subpage_content, $line;
                $subpages_printed++;
            }
        } elsif ($in_subpage_section) {
            if ($visible_subpages == $total_subpages) {
                push @subpage_content, $line;
            }
        } else {
            push @subpage_content, $line;
        }
    }

    foreach my $line (@subpage_content) {
        if ($line =~ /^\s*$/) {
            $y++;
            next;
        }

        my $x = 0;
        my $print_x = 0;

        while ($x < length($line)) {
            if ($line =~ /\G<([ygp])>/gc) {
                $current_color = $1 eq 'y' ? 1 : ($1 eq 'g' ? 2 : 3);
            }
            elsif ($line =~ /\G<\/[ygp]>/gc) {
                $current_color = 0;
            }
            else {
                my $text = $line =~ /\G(.*?)(?=<[\/ygp]{1,2}>|\z)/gc ? $1 : "";
                $window->attron(COLOR_PAIR($current_color)) if $current_color;
                $window->addstr($y, $print_x, $text);
                $window->attroff(COLOR_PAIR($current_color)) if $current_color;
                $print_x += length($text);
            }
            $x = pos($line) || length($line);
        }
        $y++;
    }

    my ($max_y, $max_x);
    $window->getmaxyx($max_y, $max_x);
    $window->move($max_y - 1, $max_x - 1);
    $window->refresh();
}

sub count_subpages {
    my ($page_content) = @_;
    return scalar grep { is_subpage($_) } split(/\n/, $page_content);
}

sub main {
    initialize_curses();

    local $/ = undef;
    my $content = <DATA>;
    my @pages = split(/------+/, $content);

    my $current_page = 0;
    my $visible_subpages = 0;

    while (1) {
        print_page($pages[$current_page], $visible_subpages);
        my $key = $window->getch();

        if ($key eq 'n') {
            if ($current_page < $#pages) {
                $current_page++;
                $visible_subpages = 0;
            }
        }
        elsif ($key eq 'p') {
            if ($current_page > 0) {
                $current_page--;
                $visible_subpages = 0;
            }
        }
        elsif ($key eq '1') {
            $current_page = 0;
            $visible_subpages = 0;
        }
        elsif ($key eq 'G') {
            $current_page = $#pages;
            $visible_subpages = 0;
        }
        elsif ($key eq 'h') {
            if ($visible_subpages > 0) {
                $visible_subpages--;
            }
            elsif ($current_page > 0) {
                $current_page--;
                $visible_subpages = 0;
            }
        }
        elsif ($key eq 'l') {
            my $subpages = count_subpages($pages[$current_page]);
            if ($visible_subpages < $subpages) {
                $visible_subpages++;
            }
            elsif ($current_page < $#pages) {
                $current_page++;
                $visible_subpages = 0;
            }
        }
        elsif ($key eq 'q') {
            last;
        }
    }

    cleanup_curses();
}

main();

__END__








                      <g>Sherlock Claude</g>

                           <g>or</g>

                      <y>Making Claude a Consulting Detective</y>




-------

<g>What this project does.<g>


<y>This program is a proof of concept testing the capabilities of chatbots via fictitious mysteries.

It does this in a very specific way that we will go into later.</y>


-------

<g>Why do this? Why mysteries?</g>


<y>Mysteries have several advantages in the use to test chatbots. 
They test, amongst other things, the chatbot's:</y>

<p>     - critical thinking and analytical skills

     - ability to create a mental map of a situation

     - attention to detail and the ability to pick out clues

     - long term and needle-in-the-haystack recall

     - creativity, to think of theories that make sense of a scenario 

     - perspective-taking skills 

     - emotional intelligence, the ability to discern human motive                                                       and human nature and infer conclusions from it


     - the ability to weigh different often conflicting theories and
       use empirical evidence to determine which ones are true.


     - overall multi-modal thinking, extracting clues from text and images.

     - planning and implementing high-level investigations</p>

-------

<g>But not all mysteries are the same!</g>


<y>It is important to consider the type of mystery we use here. Basically they are three types:</y>

<p>    - static mysteries  (short stories, books and movies). 

    - real life mysteries  

    - mystery games</p>

<y>We'll take each in turn.</y>


-------

<g>Deficiencies in Static Mysteries</g>


<y>On the surface you'd think that just feeding in detective novels 
would be an easy way to do this but there are downsides:</y>

<p>    - They are meant to be enjoyed, not solved. They often hide or otherwise give false information 
      and don't give the reader enough details to solve it themselves.


    - They do not allow for planning. The reader is at the mercy of where the writer wants to go next.


    - They don't focus on process. Instead they are more interested in painting a picture with                          a mystery as a backdrop.</p>


<p> In short, most mysteries are literature first, human puzzles second</p>


-------

<g>Deficiencies in real-life mysteries</g>


<y>Again, choosing real-life, current cases would seem ideal but they are out of scope 
for current chatbots, since they don't have the bandwidth to handle a real case. 

Interrogations, footwork, stake-outs, examination of large amounts of bookwork and 
other evidence, tripping up suspects would require a bot far more capable than available now.


If static mysteries don't allow for any planning, real-life mysteries are too broad.</y>


-------

<g>Enter the Mystery Game.</g>


<y>Mystery games offer the middle choice. There are several classes of mystery game which allow hobbyists to play detective including:</y>

<p>    - interactive video games (Chronicles of Crime, LA Noire)

    - competitive board games (Detective, Arkham)

    - Evidence hunting games (Unsolved case files, murder mystery party, Her Story)

    - straight narrative games (sherlock holmes consulting detective, gumshoe, mortum medieval detective)</p>

<p>Sherlock Claude tests the narrative form of mystery games</p>


-------
<g> Mystery Game Advantages</g>

<y>For the purposes of testing a chatbot they offer several advantages:</y>

<p>    - they have a limited number of choices. The player can choose x number of next moves and follow through. 

    - they have an answer or answers! you can readily tell if you are on the right or wrong track.

    - they are quite challenging. It often takes a lot of the skills listed above to solve them</p>


-------

<g>Project Focus</g>


<y>In this project, we've chosen Sherlock Holmes Consulting Detective. It is a straight narrative game with a fixed format in cases.

We chose it specifically because of its difficulty. It is known to be one of the most difficult of this genre of games out there, with a reputation 
for making people 'feel stupid'. It also has a large community, which discusses cases online in user groups.

The goal of this project is to simulate claude solving these cases and seeing how well it does.</y>

-------

<g>The program:</g>

<y>Enter Sherlock Claude. Sherlock Claude is simple framework that allows you to:</y>

<p>    - feed mystery premises into the chatbot

    - have a chatbot proceed to investigate these mysteries using its own skills

    - have the chatbot give a potential answer

    - determine how well the chatbot does.</p>

<y>It uses two agent instances that talk to each other:</y>

<p>    - a Referee, which knows the content of the case, and the evidence behind it.

    - an Investigator, which talks to the referee to gain clues and determine answers.</p>


<y>In short the referee knows the truth of the case and doles it out, the investigator puts together the pieces.</y>

-------

Demo


.....


-------

<g>Results</g>


.....


-------

<g>Next Steps</g>


<y>The next steps here are divided into immediate and long term.


Immediate steps here are:</y>

<p>    - uploading the fan created cases tested here to github after talking to the case owners

    - reaching out to Space Cowboys to test the rest of the published cases

    - bot investigation optimizations (memory, summarization, note taking)

    - benchmarking different claude instnaces</p>


<y>Long-term steps potentially include:</y>

<p>     - implementing different approaches to the investigation process (specialized agents)

    - branching out to other mystery games and game types

    - creating new, standardized benchmark based off a set of private cases

    - bulk generation of case training data to be used to improve models (eg. gamifying real life cases).</p>

------

<g>Takeaway</g>

<y>We have presented 'Sherlock Claude' here, which in our minds provides a valuable benchmark for 
measuring attributes of intelligence in chatbots that are under-represented in other tests.


Attributes like long term planning, emotional intelligence, mind-maps and weighing conflicting evidence,
creativity, amongst others can be evaluated subjectively.


However in the fixed mode of a game with a concrete score, this can be turned into a measurable metric.
Since the difficulty and scope of attributes needed to solve these cases is so large, it is likely to be a 
very open-ended metric.</y>


------

<g>Links</g>


<y>This project heavily relied on testing with casees from the game Sherlock's Holmes Consulting Detective. We used fan-made cases, but there are a 
series of these games sold by Space Cowboys, main site here:</y>

    <p>https://www.spacecowboys.fr/sherlock-holmes-consultingdetective</p>

<y>In particular these were helpful links:</y>

<p>    source for free, fan made cases
        https://boardgamegeek.com/thread/1576619/listing-of-all-fan-made-free-cases

    source for holmes cases/sample_case_online:
        https://images-cdn.asmodee.us/filer_public/e4/cb/e4cb5e42-c7a2-4ac0-a8d0-c0a752500b4d/shehdemo_85x11.pdf

    background video on free fan-made cases
         https://www.youtube.com/watch?v=a3X0GM--3Bk

    material needed for fan made cases

        https://www.spacecowboys.fr/case3-the-murderess
        https://www.spacecowboys.fr/sherlock-holmes-consultingdetective</p>


<y>If you have not played this game - or games like it, namely mystery games - and you are a fan of puzzles I'd highly recommend it. 
It is indeed a challenging experience - wheras watching or reading a murder mystery is a passive experience, actually trying to 
solve a mystery is a different matter, and it is quite a bit more difficult.

I highly recommend the youtube channel https://www.youtube.com/@COOPFORTWO for more of an introduction here.</y>
