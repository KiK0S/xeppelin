#include <bits/stdc++.h>
using namespace std;


using ll = long long;
using ld = long double;

#ifdef EDULCNI_ENABLED
#define var(...) EDULCNI_VAR(__VA_ARGS__)
#define read(...) EDULCNI_READ(__VA_ARGS__)
#define write(...) EDULCNI_WRITE(__VA_ARGS__)
#else
template <typename T, typename = void>
struct is_range : false_type {};

template <typename T>
struct is_range<T, void_t<
    decltype(begin(declval<T&>())),
    decltype(end(declval<T&>()))>>
    : bool_constant<!is_same_v<decay_t<T>, string>> {};

template <typename T, typename = void>
struct is_iterator : false_type {};

template <typename T>
struct is_iterator<T, void_t<
    typename iterator_traits<T>::iterator_category>> : true_type {};

template <typename T>
void print_value(ostream& output, const T& value) {
    if constexpr (is_range<T>::value) {
        output << '[';
        size_t index = 0;
        for (const auto& element : value) {
            output << (index++ == 0 ? "" : " ");
            print_value(output, element);
        }
        output << ']';
    } else {
        output << value;
    }
}

template <typename T>
void read_value(T& value) {
    if constexpr (is_range<T>::value) {
        for (auto& element : value) cin >> element;
    } else {
        cin >> value;
    }
}

template <typename... Values>
istream& read_values(Values&... values) {
    (read_value(values), ...);
    return cin;
}

template <typename Iterator,
          enable_if_t<is_iterator<Iterator>::value, int> = 0>
istream& read_values(Iterator first, Iterator last) {
    for (; first != last && cin; ++first) cin >> *first;
    return cin;
}

template <typename T>
void write_value(ostream& output, bool& first, const T& value) {
    if constexpr (is_range<T>::value) {
        for (const auto& element : value) write_value(output, first, element);
    } else {
        output << (first ? "" : " ") << value;
        first = false;
    }
}

template <typename... Values>
ostream& write_values(const Values&... values) {
    bool first = true;
    (write_value(cout, first, values), ...);
    return cout << '\n';
}

template <typename Iterator,
          enable_if_t<is_iterator<Iterator>::value, int> = 0>
ostream& write_values(Iterator first, Iterator last) {
    bool first_value = true;
    for (; first != last; ++first) write_value(cout, first_value, *first);
    return cout << '\n';
}

#ifdef DEBUG
template <typename... Values>
void log_values(const char* operation, const char* names,
                const char* file, int line, const Values&... values) {
    cerr << file << ':' << line << " | " << operation << " | "
         << names << ": ";
    size_t index = 0;
    ((cerr << (index++ == 0 ? "" : " "), print_value(cerr, values)), ...);
    cerr << '\n';
}

template <typename Iterator,
          enable_if_t<is_iterator<Iterator>::value, int> = 0>
void log_values(const char* operation, const char* names,
                const char* file, int line, Iterator first, Iterator last) {
    cerr << file << ':' << line << " | " << operation << " | "
         << names << ": [";
    size_t index = 0;
    for (; first != last; ++first) {
        cerr << (index++ == 0 ? "" : " ");
        print_value(cerr, *first);
    }
    cerr << "]\n";
}

template <typename... Values>
istream& debug_read(const char* names, const char* file, int line,
                    Values&... values) {
    istream& result = read_values(values...);
    log_values("read", names, file, line, values...);
    return result;
}

template <typename Iterator,
          enable_if_t<is_iterator<Iterator>::value, int> = 0>
istream& debug_read(const char* names, const char* file, int line,
                    Iterator first, Iterator last) {
    istream& result = read_values(first, last);
    log_values("read", names, file, line, first, last);
    return result;
}

template <typename... Values>
ostream& debug_write(const char* names, const char* file, int line,
                     const Values&... values) {
    ostream& result = write_values(values...);
    log_values("write", names, file, line, values...);
    return result;
}

template <typename Iterator,
          enable_if_t<is_iterator<Iterator>::value, int> = 0>
ostream& debug_write(const char* names, const char* file, int line,
                     Iterator first, Iterator last) {
    ostream& result = write_values(first, last);
    log_values("write", names, file, line, first, last);
    return result;
}

#define read(...) debug_read(#__VA_ARGS__, __FILE__, __LINE__, __VA_ARGS__)
#define write(...) debug_write(#__VA_ARGS__, __FILE__, __LINE__, __VA_ARGS__)
#define var(...) log_values("var", #__VA_ARGS__, __FILE__, __LINE__, __VA_ARGS__)
#else
#define read(...) read_values(__VA_ARGS__)
#define write(...) write_values(__VA_ARGS__)
#define cerr if (false) cerr
#define var(...)
#endif
#endif

#define pii pair<int, int>
#define tup(x, i) get<i>(x)
#define F first
#define S second
#define all(v) v.begin(), v.end()
#define forn(i, n) for (int i = 0; i < n; i++)
#define vi vector<int>

#define int ll

const int MAXN = 1e6 + 10;
int n;

void solve() {

}

signed main() {
    #ifdef DEBUG
    freopen("input.in", "r", stdin);
    freopen("output.out", "w", stdout);
    #endif
    ios_base::sync_with_stdio(0); cin.tie(0);
    int _t; read(_t);
    while (read(n)) solve();
    cerr << "Runtime is: " << clock() * 1.0 / CLOCKS_PER_SEC << endl;
}
